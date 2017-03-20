import datetime
import json

from passlib.hash import sha256_crypt
from peewee import SqliteDatabase, MySQLDatabase, CharField, BooleanField, ForeignKeyField, IntegerField, DateTimeField, \
    OperationalError, Model
from pywebpush import WebPusher

from home.core.utils import random_string
from settings import GOOGLE_API_KEY

if True:
    db = SqliteDatabase('app.db')
else:
    db = MySQLDatabase(host="localhost", database="party", user="party", passwd="party")


def db_init():
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
            u = User.create(username='keane', password="")
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

    def is_active(self):
        return True

    def get_id(self):
        return self.username

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def check_password(self, password):
        return sha256_crypt.verify(password, self.password)

    def set_password(self, password):
        self.password = sha256_crypt.encrypt(password)


class APIClient(BaseModel):
    name = CharField(unique=True)
    token = CharField(default=random_string)


class Subscriber(BaseModel):
    endpoint = CharField(unique=True)
    auth = CharField()
    p256dh = CharField()
    user = ForeignKeyField(User, related_name='subscribers')

    def to_dict(self):
        return {
            'endpoint': self.endpoint,
            'keys': {'auth': self.auth,
                     'p256dh': self.p256dh
                     }
            }

    def push(self, message):
        WebPusher(self.to_dict()).send(
            json.dumps({'body': message,
                        'icon': 'https://105ww.xyz/static/favicon.ico'}),
            gcm_key=GOOGLE_API_KEY)


class SecurityController(BaseModel):
    state = CharField(default='disabled')

    def arm(self):
        self.state = 'armed'
        self.save()

    def occupied(self):
        self.state = 'occupied'
        self.save()

    def alert(self):
        self.state = 'alert'
        self.save()

    def disable(self):
        self.state = 'disabled'
        self.save()

    def is_alert(self):
        return self.state == 'alert'

    def is_armed(self):
        return self.state == 'armed'


class SecurityEvent(BaseModel):
    controller = ForeignKeyField(SecurityController, related_name='events')
    device = CharField()
    in_progress = BooleanField(default=True)
    datetime = DateTimeField(default=datetime.datetime.now)
    duration = IntegerField(null=True)
