import json

import datetime
from passlib.hash import sha256_crypt
from peewee import SqliteDatabase, MySQLDatabase, CharField, BooleanField, ForeignKeyField, IntegerField, \
    DateTimeField, \
    OperationalError, Model
from pywebpush import WebPusher
from typing import List, Dict

from home.core.utils import random_string
from home.settings import GOOGLE_API_KEY, USE_LDAP

if True:
    db = SqliteDatabase('app.db')
else:
    db = MySQLDatabase(host="localhost", database="party", user="party", passwd="party")


def db_init() -> None:
    db.connect()
    try:
        db.create_tables([User,
                          Subscriber,
                          SecurityController,
                          SecurityEvent,
                          APIClient
                          ])
        print('Creating tables...')
        # TODO: fix to use app.debug
        if True:
            u = User.create(username='root', password="")
            User.create(username='guest', password="")
            u.set_password('root')
            u.admin = True
            u.save()
            SecurityController.create()
    except OperationalError:
        pass
    db.close()


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True)
    authenticated = BooleanField(default=False)
    password = CharField()
    admin = BooleanField(default=False)
    _groups = CharField(default='')
    ldap = BooleanField(default=False)

    def is_active(self) -> bool:
        return True

    def get_id(self) -> str:
        return self.username

    def is_authenticated(self) -> bool:
        return self.authenticated

    def is_anonymous(self) -> bool:
        return False

    def check_password(self, password: str) -> bool:
        if self.ldap and USE_LDAP:
            from home.web.utils import ldap_auth
            return ldap_auth(self.username, password)
        return sha256_crypt.verify(password, self.password)

    def set_password(self, password: str) -> None:
        self.password = sha256_crypt.encrypt(password)

    @property
    def groups(self) -> List[str]:
        return self._groups.split(',')


class APIClient(BaseModel):
    name = CharField(unique=True)
    token = CharField(default=random_string)


class Subscriber(BaseModel):
    endpoint = CharField(unique=True)
    auth = CharField()
    p256dh = CharField()
    user = ForeignKeyField(User, related_name='subscribers')

    def to_dict(self) -> Dict[str, str]:
        return {
            'endpoint': self.endpoint,
            'keys': {'auth': self.auth,
                     'p256dh': self.p256dh
                     }
            }

    def push(self, message: str, icon: str = '/static/favicon.ico') -> None:
        WebPusher(self.to_dict()).send(
            json.dumps({'body': message,
                        'icon': icon}),
            gcm_key=GOOGLE_API_KEY)


class SecurityController(BaseModel):
    state = CharField(default='disabled')

    def arm(self) -> None:
        self.state = 'armed'
        self.save()

    def occupied(self) -> None:
        self.state = 'occupied'
        self.save()

    def alert(self) -> None:
        self.state = 'alert'
        self.save()

    def disable(self) -> None:
        self.state = 'disabled'
        self.save()

    def is_alert(self) -> bool:
        return self.state == 'alert'

    def is_armed(self) -> bool:
        return self.state == 'armed'


class SecurityEvent(BaseModel):
    controller = ForeignKeyField(SecurityController, related_name='events')
    device = CharField()
    in_progress = BooleanField(default=True)
    datetime = DateTimeField(default=datetime.datetime.now)
    duration = IntegerField(null=True)
    #new = BooleanField(default=True)
