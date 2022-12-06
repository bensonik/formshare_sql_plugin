import formshare.plugins as plugins
import formshare.plugins.utilities as u
from .views import (
    ExecuteSQL,
    GetDatabases,
    GetTables,
    GetFields,
    CheckTaskStatus,
    GetTaskResult,
)


class RemoteSQL(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IDatabase)

    def before_mapping(self, config):
        # We don't add any routes before the host application
        return []

    def after_mapping(self, config):
        # We add here a new route /json that returns a JSON
        custom_map = [
            u.add_route(
                "execute_remote_sql",
                "/user/{userid}/analytics/tools/remote_sql/execute",
                ExecuteSQL,
                None,
            ),
            u.add_route(
                "get_task_status",
                "/user/{userid}/analytics/tools/remote_sql/task_status",
                CheckTaskStatus,
                None,
            ),
            u.add_route(
                "get_task_result",
                "/user/{userid}/analytics/tools/remote_sql/task_result",
                GetTaskResult,
                None,
            ),
            u.add_route(
                "get_databases",
                "/user/{userid}/analytics/tools/remote_sql/databases",
                GetDatabases,
                None,
            ),
            u.add_route(
                "get_tables",
                "/user/{userid}/analytics/tools/remote_sql/tables",
                GetTables,
                None,
            ),
            u.add_route(
                "get_fields",
                "/user/{userid}/analytics/tools/remote_sql/fields",
                GetFields,
                None,
            ),
        ]

        return custom_map

    def update_orm(self, config):
        config.include("remoteSQL.orm")

    def update_extendable_tables(self, tables_allowed):
        tables_allowed.append("remote_sql_task")
        return tables_allowed

    def update_extendable_modules(self, modules_allowed):
        modules_allowed.append("remoteSQL.orm.tasks")
        return modules_allowed
