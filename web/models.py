import ast
import uuid
import json
import datetime

from peewee import *
from passlib.hash import sha256_crypt

from main import app

# Based on configuration, use a different database.
if app.debug:
    db = SqliteDatabase('app.db')
else:
    db = MySQLDatabase(host="localhost", database="party", user="party", passwd="party")

def db_init():
    db.connect()
    try:
        db.create_tables([User, Subscriber,
                          SecurityController, SecurityEvent,])
        print('Creating tables...')
        if app.debug:
            u = User.create(username='keane', password="")
            u.set_password('root')
            u.admin = True
            u.save()
            SecurityController.create()
            Sensor.create(name='cam1', typeof='camera', key='cam1')
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


class SecurityEvent(BaseModel):
    controller = ForeignKeyField(SecurityController, related_name='events')
    device = CharField()
    in_progress = BooleanField(default=True)
    datetime = DateTimeField(default=datetime.datetime.now)
