import datetime
import json
from typing import List, Dict

from flask_login import UserMixin
from passlib.hash import sha256_crypt
from peewee import CharField, BooleanField, ForeignKeyField, IntegerField, \
    DateTimeField, \
    OperationalError, Model
from pywebpush import WebPusher

from home.core.utils import random_string
from home.settings import GOOGLE_API_KEY, USE_LDAP, db, DEBUG

grants = []


def db_init() -> None:
    db.connect()
    try:
        db.create_tables([User,
                          Subscriber,
                          SecurityController,
                          SecurityEvent,
                          APIClient,
                          OAuthClient
                          ])
        print('Creating tables...')
        if DEBUG:
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


class User(BaseModel, UserMixin):
    username = CharField(unique=True)
    authenticated = BooleanField(default=False)
    password = CharField()
    admin = BooleanField(default=False)
    _groups = CharField(default='')
    ldap = BooleanField(default=False)

    def get_id(self) -> str:
        return self.username

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
    permissions = CharField(default='')

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions.split(',')

    def add_permission(self, permission: str) -> None:
        permission = permission.replace(' ', '')
        if not self.has_permission(permission):
            if self.permissions and not self.permissions[-1] == ',':
                self.permissions += ','
            self.permissions += permission + ','
            self.save()


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
    # new = BooleanField(default=True)


class OAuthClient(BaseModel):
    name = CharField()
    user = ForeignKeyField(User, related_name='oauth_clients')

    client_id = CharField(primary_key=True)
    client_secret = CharField(unique=True)


class Token(BaseModel):
    client = ForeignKeyField(OAuthClient, related_name='tokens')
    user = ForeignKeyField(User, related_name='tokens')
    token_type = CharField()
    access_token = CharField(unique=True)
    refresh_token = CharField(unique=True)
    expires = DateTimeField()
    _scopes = CharField(null=True)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class Grant:
    def __init(self, user: User, client_id: str, client: OAuthClient, code: str, redirect_uri: str, _scopes: str,
               expires: datetime.date):
        self.user = user
        self.client_id = client_id
        self.client = client
        self.code = code
        self.redirect_uri = redirect_uri
        self._scopes = _scopes
        self.expires = expires
