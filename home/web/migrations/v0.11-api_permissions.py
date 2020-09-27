#!/usr/bin/env python3
from playhouse.migrate import *

from home.settings import db
from home.web.migrations.utils import get_migrator

migrator = get_migrator(db)

with db.transaction():
    migrate(
        migrator.add_column('apiclient', 'permissions', CharField(default='')),
    )
