from formshare.plugins.utilities import FormSharePrivateView
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
import urllib.parse as parse
from subprocess import Popen, PIPE
import zipfile
from formshare.processes.db import get_query_user, get_query_password
from formshare.config.encdecdata import decode_data
import os
import uuid
from pyramid.response import FileResponse


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
            raise HTTPForbidden
        if self.request.params.get("async", "false") == "false":
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
            if mysql_user is not None:
                mysql_password = get_query_password(self.request, user_id)
                mysql_password = decode_data(
                    self.request, mysql_password.encode()
                ).decode()
                mysql_password = parse.quote(mysql_password)
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
                        zip_file, request=self.request, content_type="application/csv"
                    )
                    response.content_disposition = (
                        'attachment; filename="' + 'result.zip"'
                    )
                    return response
                except Exception as e:
                    raise self.append_to_errors(str(e))
            else:
                self.append_to_errors("You haven't activated the analytics module")
        else:
            pass
