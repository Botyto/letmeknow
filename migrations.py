import alembic.command
import alembic.config
import logging
import os
import shutil
import sqlalchemy.sql

import db

logger = logging.getLogger(__name__)


class MigrationsManager:
    env: dict
    config: alembic.config.Config
    migrations_path: str

    def __init__(self, env: dict):
        self.env = env
        ini_path = os.path.join(env.get("temp_path"), "migrations.ini")
        self._update_ini(ini_path)
        self.config = alembic.config.Config(ini_path)
        self.migrations_path = "migrations"

    def _update_ini(self, ini_path: str):
        if os.path.isfile(ini_path):
            os.remove(ini_path)
        with open(ini_path, "wt") as fh:
            fh.write("\n".join([
                "[alembic]",
                "file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d_%%(minute).2d_%%(rev)s_%%(slug)s",
                "script_location = migrations",
                "prepend_sys_path = .",
                "version_path_separator = os",
                "sqlalchemy.url = " + self.context.database_manager.admin_connection_string,
                "[loggers]",
                "keys = root,sqlalchemy,alembic",
                "[handlers]",
                "keys = console",
                "[formatters]",
                "keys = generic",
                "[logger_root]",
                "level = WARN",
                "handlers = console",
                "qualname =",
                "[logger_sqlalchemy]",
                "level = WARN",
                "handlers =",
                "qualname = sqlalchemy.engine",
                "[logger_alembic]",
                "level = INFO",
                "handlers =",
                "qualname = alembic",
                "[handler_console]",
                "class = StreamHandler",
                "args = (sys.stderr,)",
                "level = NOTSET",
                "formatter = generic",
                "[formatter_generic]",
                "format = %(levelname)-5.5s [%(name)s] %(message)s",
                "datefmt = %H:%M:%S",
            ]))

    def init(self):
        logger.info("Installing migrations system")
        alembic.command.init(self.config, self.migrations_path)
        # automatically edit ./migrations/env.py
        env_py_path = "./migrations/env.py"
        with open(env_py_path, "rt") as envf:
            env_py_code = envf.read()
        env_py_code = env_py_code.replace(
            "target_metadata = None",
            "import system.application.database\n" +
            "target_metadata = system.application.database.Model.metadata")
        with open(env_py_path, "wt") as envf:
            envf.write(env_py_code)
        # automatically edit ./migrations.ini
        migrations_init_path = "./migrations.ini"
        with open(migrations_init_path, "rt") as envf:
            migrations_ini_code = envf.read()
        migrations_ini_code = migrations_ini_code.replace(
            "sqlalchemy.url = driver://user:pass@localhost/dbname",
            "sqlalchemy.url = " + self.context.database_manager.connection_string)
        with open(migrations_init_path, "wt") as envf:
            envf.write(migrations_ini_code)
        # delete unnecessary README
        readme_path = "./migrations/README"
        if os.path.isfile(readme_path):
            os.remove(readme_path)
        logger.info("Done!")

    def generate(self, title: str):
        logger.info("Generating a new migration '%s'", title)
        alembic.command.revision(self.config, title, True)
        logger.info("Done!")

    def update(self):
        logger.info("Updating the database schema to the latest version")
        alembic.command.upgrade(self.config, "head")
        logger.info("Done!")

    def uninstall(self):
        logger.info("Uninstalling the database")
        # drop all tables
        tables = db.Model.metadata.sorted_tables
        logger.info("Will empty %s tables", len(tables))
        db.engine.execute("SET foreign_key_checks = 0;")
        statement = "\n".join([f"TRUNCATE `{t.name}`;" for t in tables])
        statement = sqlalchemy.sql.text(statement)
        db.engine.execute(statement)
        db.engine.execute("SET foreign_key_checks = 1;")
        logger.info("Database tables emptied")
        # remove all local file data
        appdata_path = "data"
        if os.path.isdir(appdata_path):
            logger.info("Deleting application data directory '%s'", appdata_path)
            shutil.rmtree(appdata_path)
        logger.info("Done!")
