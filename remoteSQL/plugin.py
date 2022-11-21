import formshare.plugins as plugins
import formshare.plugins.utilities as u
from .views import ExecuteSQL
import sys
import os


class RemoteSQL(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IConfig)
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
        ]

        return custom_map

    def update_config(self, config):
        # We add here the templates of the plugin to the config
        u.add_templates_directory(config, "templates")

    def update_orm(self, config):
        config.include("remoteSQL.orm")

    def update_extendable_tables(self, tables_allowed):
        tables_allowed.append("remote_sql_task")
        return tables_allowed

    def update_extendable_modules(self, modules_allowed):
        modules_allowed.append("remoteSQL.orm.tasks")
        return modules_allowed
