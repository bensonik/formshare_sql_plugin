from formshare.models.meta import Base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Unicode,
)
from sqlalchemy.orm import relationship


class RemoteSQLTask(Base):
    __tablename__ = "remote_sql_task"

    task_id = Column(Unicode(64), primary_key=True)
    user_id = Column(
        ForeignKey("fsuser.user_id", ondelete="CASCADE"),
        index=True,
    )
    task_cdate = Column(DateTime)
    task_file = Column(Unicode(64))

    project = relationship("Project")
