from peewee import SqliteDatabase, MySQLDatabase
from playhouse.migrate import SqliteMigrator, MySQLMigrator


def get_migrator(db):
    if type(db) == SqliteDatabase:
        return SqliteMigrator(db)
    elif type(db) == MySQLDatabase:
        return MySQLMigrator(db)
