#!/usr/bin/env python3
from playhouse.migrate import *

from home.settings import db


if type(db) == SqliteDatabase:
    migrator = SqliteMigrator()
elif type(db) == MySQLDatabase:
    migrator = MySQLMigrator(db)

with db.transaction():
    migrate(
        migrator.add_column('apiclient', 'permissions', CharField(default='')),
    )
