#!/usr/bin/env python3
from secrets import token_hex

from playhouse.migrate import *

from home.settings import db


if type(db) == SqliteDatabase:
    migrator = SqliteMigrator(db)
elif type(db) == MySQLDatabase:
    migrator = MySQLMigrator(db)

with db.transaction():
    migrate(
        migrator.add_column('user', 'token', CharField(default=token_hex)),
    )
