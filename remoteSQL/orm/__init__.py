from formshare.models.schema import initialize_schema
from sqlalchemy.orm import configure_mappers

from remoteSQL.orm.tasks import RemoteSQLTask

configure_mappers()


def includeme(config):
    initialize_schema()
