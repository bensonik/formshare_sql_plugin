"""Initial DB structure

Revision ID: cd44348b274f
Revises: 
Create Date: 2022-11-21 10:04:21.440863

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "cd44348b274f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "remote_sql_task",
        sa.Column("task_id", sa.Unicode(length=64), nullable=False),
        sa.Column("user_id", sa.Unicode(length=120), nullable=True),
        sa.Column("task_cdate", sa.DateTime(), nullable=True),
        sa.Column(
            "task_file", mysql.MEDIUMTEXT(collation="utf8mb4_unicode_ci"), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["fsuser.user_id"],
            name=op.f("fk_remote_sql_task_user_id_fsuser"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", name=op.f("pk_remote_sql_task")),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_index(
        op.f("ix_remote_sql_task_user_id"), "remote_sql_task", ["user_id"], unique=False
    )


def downgrade():
    op.drop_table("remote_sql_task")
