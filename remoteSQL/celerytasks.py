from formshare.config.celery_app import celeryApp
from formshare.config.celery_class import CeleryTask
from subprocess import Popen, PIPE
import zipfile


class ExecutionError(Exception):
    """
    Exception raised when there is an error while creating the repository.
    """


@celeryApp.task(bind=True, base=CeleryTask)
def execute_sql_async(
    self,
    mysql_host,
    mysql_port,
    mysql_user,
    mysql_password,
    mysql_database,
    sql,
    output_format,
    output_file,
    zip_file,
):
    uri = (
        mysql_user
        + ":"
        + mysql_password
        + "@"
        + mysql_host
        + ":"
        + mysql_port
        + "/"
        + mysql_database
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
        stdout, stderr = p.communicate(input=sql.encode())
        if p.returncode != 0:
            error_array = stderr.decode().split("\n")
            if len(error_array) > 1:
                raise ExecutionError(error_array[1])
            else:
                raise ExecutionError(error_array[0])
    try:
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(output_file, zip_filename)
    except Exception as e:
        raise ExecutionError(str(e))
