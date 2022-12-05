from formshare.plugins.utilities import FormSharePrivateView
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
import urllib.parse as parse
from subprocess import Popen, PIPE
import zipfile
from formshare.processes.db import (
    get_query_user,
    get_query_password,
    get_task_status,
    get_user_databases,
    get_dictionary_tables,
    get_forms_for_schema,
    get_project_for_schema,
    get_dictionary_fields,
)
from formshare.config.encdecdata import decode_data
import os
import uuid
from pyramid.response import FileResponse
from remoteSQL.celerytasks import execute_sql_async
from remoteSQL.orm.tasks import add_task, task_exist, get_task_file


class ExecuteSQL(FormSharePrivateView):
    def process_view(self):
        if not self.api:
            raise HTTPBadRequest
        if self.request.method != "POST":
            raise HTTPBadRequest
        request_data = self.get_post_dict()
        if "sql" not in request_data.keys():
            raise HTTPBadRequest
        user_id = self.request.matchdict["userid"]
        if user_id != self.user.login:
            raise HTTPNotFound

        if self.request.params.get("format", "json") != "json":
            output_format = "tab"
        else:
            output_format = "json"
        temp_directory = str(uuid.uuid4())
        repository_path = self.request.registry.settings["repository.path"]
        paths = ["tmp", temp_directory]
        temp_dir = os.path.join(repository_path, *paths)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        paths = ["tmp", temp_directory, temp_directory + "." + output_format]
        output_file = os.path.join(repository_path, *paths)
        paths = ["tmp", temp_directory, temp_directory + ".zip"]
        zip_file = os.path.join(repository_path, *paths)

        mysql_host = self.request.registry.settings.get("mysql.host")
        mysql_port = self.request.registry.settings.get("mysql.port")
        mysql_user = parse.quote(get_query_user(self.request, user_id))
        mysql_password = get_query_password(self.request, user_id)
        mysql_password = decode_data(self.request, mysql_password.encode()).decode()
        mysql_password = parse.quote(mysql_password)
        if mysql_user is not None:
            if self.request.params.get("async", "false") == "false":
                uri = (
                    mysql_user
                    + ":"
                    + mysql_password
                    + "@"
                    + mysql_host
                    + ":"
                    + mysql_port
                    + "/"
                    + mysql_user
                )
                args = ["mysqlsh", "--sql", "--uri=" + uri]
                if output_format == "json":
                    args.append("--result-format=json/array")
                    zip_filename = "output.json"
                else:
                    args.append("--result-format=tabbed")
                    zip_filename = "output.tab"
                with open(output_file, "wb") as out:
                    p = Popen(args, stdout=out, stderr=PIPE, stdin=PIPE)
                    stdout, stderr = p.communicate(input=request_data["sql"].encode())
                    if p.returncode != 0:
                        error_array = stderr.decode().split("\n")
                        if len(error_array) > 1:
                            self.append_to_errors(error_array[1])
                        else:
                            self.append_to_errors(error_array[0])
                try:
                    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
                        zf.write(output_file, zip_filename)
                    response = FileResponse(
                        zip_file, request=self.request, content_type="application/zip"
                    )
                    response.content_disposition = (
                        'attachment; filename="' + 'result.zip"'
                    )
                    self.returnRawViewResult = True
                    return response
                except Exception as e:
                    raise self.append_to_errors(str(e))
            else:
                task = execute_sql_async.apply_async(
                    (
                        mysql_host,
                        mysql_port,
                        mysql_user,
                        mysql_password,
                        request_data["sql"],
                        output_format,
                        output_file,
                        zip_file,
                    ),
                    queue="FormShare",
                )
                add_task(self.request, user_id, task.id, zip_file)
                return {"task_id": task.id}
        else:
            self.append_to_errors("You haven't activated the analytics module")
        return {}


class CheckTaskStatus(FormSharePrivateView):
    def process_view(self):
        if not self.api:
            raise HTTPBadRequest
        if self.request.method != "POST":
            raise HTTPBadRequest
        request_data = self.get_post_dict()
        if "task" not in request_data.keys():
            raise HTTPBadRequest
        user_id = self.request.matchdict["userid"]
        if user_id != self.user.login:
            raise HTTPNotFound
        if task_exist(self.request, user_id, request_data["task"]):
            status, message = get_task_status(self.request, request_data["task"])
            if status == -1:
                return {"status": "running"}
            else:
                if status == 0:
                    return {"status": "finished"}
                else:
                    return {"status": "error", "error": message}
        else:
            self.append_to_errors("Such task does not exists")
        return {}


class GetTaskResult(FormSharePrivateView):
    def process_view(self):
        if not self.api:
            raise HTTPBadRequest
        if self.request.method != "POST":
            raise HTTPBadRequest
        request_data = self.get_post_dict()
        if "task" not in request_data.keys():
            raise HTTPBadRequest
        user_id = self.request.matchdict["userid"]
        if user_id != self.user.login:
            raise HTTPNotFound
        if task_exist(self.request, user_id, request_data["task"]):
            status, message = get_task_status(self.request, request_data["task"])
            if status == 0:
                task_file = get_task_file(self.request, user_id, request_data["task"])
                if task_file is not None:
                    response = FileResponse(
                        task_file, request=self.request, content_type="application/zip"
                    )
                    response.content_disposition = (
                        'attachment; filename="' + 'result.zip"'
                    )
                    self.returnRawViewResult = True
                    return response
                else:
                    self.append_to_errors("Unable to return file")
            else:
                if status == -1:
                    self.append_to_errors("Such task hasn't finish")
                else:
                    self.append_to_errors("Such task finished with an error")
        else:
            self.append_to_errors("Such task does not exists")
        return {}


class GetDatabases(FormSharePrivateView):
    def process_view(self):
        if not self.api:
            raise HTTPBadRequest
        user_id = self.request.matchdict["userid"]
        if user_id != self.user.login:
            raise HTTPNotFound
        mysql_user = parse.quote(get_query_user(self.request, user_id))
        if mysql_user is not None:
            databases = get_user_databases(self.request, user_id)
            for a_database in databases:
                a_database.pop("access_type", None)
            databases.append(
                {
                    "project_id": "NA",
                    "project_code": "NA",
                    "project_name": "NA",
                    "form_id": "NA",
                    "form_name": "NA",
                    "form_schema": mysql_user,
                    "form_schema_description": "Personal repository",
                }
            )
            return {"databases": databases}
        else:
            self.append_to_errors("You haven't activated the analytics module")
        return {}


def _get_repository_tables(request, project_id, schema):
    tables = []
    forms = get_forms_for_schema(request, schema)
    for a_form in forms:
        form_tables = get_dictionary_tables(request, project_id, a_form, None)
        for a_form_table in form_tables:
            table_exist = False
            for a_table in tables:
                if a_table["table_name"] == a_form_table["table_name"]:
                    table_exist = True
                    break
            if not table_exist:
                table_type = "DATA TABLE"
                if a_form_table["table_lkp"] == 1:
                    table_type = "LOOKUP TABLE"
                if a_form_table["table_name"].find("_msel_"):
                    table_type = "MULTISELECT TABLE"
                tables.append(
                    {
                        "table_name": a_form_table["table_name"],
                        "table_desc": a_form_table["table_desc"],
                        "table_type": table_type,
                    }
                )
    return tables


def _get_user_tables(request, schema):
    sql = "show full tables in {}" + schema
    tables = request.dbsession.execute(sql).fetchall()
    result = []
    for a_table in tables:
        if a_table[1] == "BASE TABLE":
            table_type = "USER TABLE"
            table_desc = "User generated table"
        else:
            table_type = "USER VIEW"
            table_desc = "User generated View"
        result.append(
            {
                "table_name": a_table[0],
                "table_type": table_type,
                "table_desc": table_desc,
            }
        )
    return result


class GetTables(FormSharePrivateView):
    def process_view(self):
        if not self.api:
            raise HTTPBadRequest
        if self.request.method != "POST":
            raise HTTPBadRequest
        request_data = self.get_post_dict()
        if "schema" not in request_data.keys():
            raise HTTPBadRequest
        user_id = self.request.matchdict["userid"]
        if user_id != self.user.login:
            raise HTTPNotFound
        mysql_user = parse.quote(get_query_user(self.request, user_id))
        if request_data["schema"] == mysql_user:
            return {"tables": _get_user_tables(self.request, request_data["schema"])}
        else:
            databases = get_user_databases(self.request, user_id)
            schema_found = False
            for a_database in databases:
                if a_database["form_schema"] == request_data["schema"]:
                    schema_found = True
                    break
            if schema_found:
                project_id = get_project_for_schema(
                    self.request, request_data["schema"]
                )
                return {
                    "tables": _get_repository_tables(
                        self.request, project_id, request_data["schema"]
                    )
                }
            else:
                self.append_to_errors(
                    "Such schema does not exists or you don't have access to it"
                )
        return {"tables": []}


class GetFields(FormSharePrivateView):
    def process_view(self):
        if not self.api:
            raise HTTPBadRequest
        if self.request.method != "POST":
            raise HTTPBadRequest
        request_data = self.get_post_dict()
        if "schema" not in request_data.keys():
            raise HTTPBadRequest
        if "table" not in request_data.keys():
            raise HTTPBadRequest
        user_id = self.request.matchdict["userid"]
        if user_id != self.user.login:
            raise HTTPNotFound
        mysql_user = parse.quote(get_query_user(self.request, user_id))
        tables = []
        project_id = None
        if request_data["schema"] == mysql_user:
            tables = _get_user_tables(self.request, request_data["schema"])
        else:
            databases = get_user_databases(self.request, user_id)
            schema_found = False
            for a_database in databases:
                if a_database["form_schema"] == request_data["schema"]:
                    schema_found = True
                    break
            if schema_found:
                project_id = get_project_for_schema(
                    self.request, request_data["schema"]
                )
                tables = _get_repository_tables(
                    self.request, project_id, request_data["schema"]
                )
            else:
                self.append_to_errors(
                    "Such schema does not exists or you don't have access to it"
                )
        table_exist = False
        for a_table in tables:
            if a_table["table_name"] == request_data["table"]:
                table_exist = True
                break
        if table_exist:
            if request_data["schema"] == mysql_user:
                sql = "DESC {}.{}"
                fields = self.request.dbsession.execute(sql).fetchall()
                result = []
                for a_field in fields:
                    result.append(
                        {
                            "field_name": a_field[0],
                            "field_type": a_field[1],
                            "field_desc": "NA",
                            "field_key": "NA",
                            "field_rtable": "NA",
                            "field_rfield": "NA",
                            "field_rlookup": "NA",
                            "field_sensitive": "NA",
                        }
                    )
                return {"fields": result}
            else:
                fields = []
                forms = get_forms_for_schema(self.request, request_data["schema"])
                for a_form in forms:
                    dict_fields = get_dictionary_fields(
                        self.request, project_id, a_form, request_data["table"]
                    )
                    for a_dict_field in dict_fields:
                        field_exist = False
                        for a_field in fields:
                            if a_field["field_name"] == a_dict_field["field_name"]:
                                field_exist = True
                                break
                        if not field_exist:
                            field_type = a_dict_field["field_type"]
                            field_size = a_dict_field["field_size"]
                            field_decsize = a_dict_field["field_decsize"]
                            if field_type == "varchar" or field_type == "int":
                                field_type = field_type + "({})".format(field_size)
                            if field_type == "decimal":
                                field_type = field_type + "({},{})".format(
                                    field_size, field_decsize
                                )

                            fields.append(
                                {
                                    "field_name": a_dict_field["field_name"],
                                    "field_type": field_type,
                                    "field_desc": a_dict_field["field_desc"],
                                    "field_key": bool(a_dict_field["field_key"]),
                                    "field_rtable": a_dict_field["field_rtable"],
                                    "field_rfield": a_dict_field["field_rfield"],
                                    "field_rlookup": bool(
                                        a_dict_field["field_rlookup"]
                                    ),
                                    "field_sensitive": bool(
                                        a_dict_field["field_sensitive"]
                                    ),
                                }
                            )
                return {"fields": fields}
        else:
            self.append_to_errors("Such table does not exists")
        return {"fields": []}
