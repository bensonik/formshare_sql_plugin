from remoteSQL.orm.remoteSQL import RemoteSQLTask
import datetime
import logging

log = logging.getLogger("formshare")


def add_task(request, user_id, task_id, task_file):
    new_task = RemoteSQLTask(
        task_id=task_id,
        user_id=user_id,
        task_cdate=datetime.datetime.now(),
        task_file=task_file,
    )
    try:
        request.dbsession.add(new_task)
        request.dbsession.flush()
        return True, ""
    except Exception as e:
        request.dbsession.rollback()
        log.error("Error {} while adding product instance".format(str(e)))
        return False, str(e)


def task_exist(request, user_id, task_id):
    res = (
        request.dbsession.query(RemoteSQLTask)
        .filter(RemoteSQLTask.user_id == user_id)
        .filter(RemoteSQLTask.task_id == task_id)
        .first()
    )
    if res is not None:
        return True
    return False


def get_task_file(request, user_id, task_id):
    res = (
        request.dbsession.query(RemoteSQLTask)
        .filter(RemoteSQLTask.user_id == user_id)
        .filter(RemoteSQLTask.task_id == task_id)
        .first()
    )
    if res is not None:
        return res.task_file
    else:
        return None
