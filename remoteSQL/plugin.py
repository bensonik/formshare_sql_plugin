import formshare.plugins as plugins
import formshare.plugins.utilities as u
from .views import MyPublicView, MyPrivateView
import sys
import os


class remoteSQL(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IConfig)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IDatabase)

    def before_mapping(self, config):
        # We don't add any routes before the host application
        return []

    def after_mapping(self, config):
        # We add here a new route /json that returns a JSON
        custom_map = [
            u.add_route(
                "plugin_mypublicview", "/mypublicview", MyPublicView, "public.jinja2"
            ),
            u.add_route(
                "plugin_myprivateview",
                "/user/{userid}/myprivateview",
                MyPrivateView,
                "private.jinja2",
            ),
        ]

        return custom_map

    def update_config(self, config):
        # We add here the templates of the plugin to the config
        u.add_templates_directory(config, "templates")

    def get_translation_directory(self):
        module = sys.modules["remoteSQL"]
        return os.path.join(os.path.dirname(module.__file__), "locale")

    def get_translation_domain(self):
        return "remoteSQL"

    def update_orm(self, config):
        config.include("remoteSQL.orm")

    def update_extendable_tables(self, tables_allowed):
        tables_allowed.append("remoteSQL_example")
        return tables_allowed

    def update_extendable_modules(self, modules_allowed):
        modules_allowed.append("remoteSQL.orm.remoteSQL")
        return modules_allowed