#!/usr/bin/env python3

from playhouse.migrate import *

from home.settings import db
from home.web import gen_token, User

if type(db) == SqliteDatabase:
    migrator = SqliteMigrator(db)
elif type(db) == MySQLDatabase:
    migrator = MySQLMigrator(db)

with db.transaction():
    migrate(
        migrator.add_column('user', 'token', CharField(unique=True)),
    )

for user in User.select():
    user.token = gen_token()
    user.save()
