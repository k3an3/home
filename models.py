from peewee import *
from passlib.hash import sha256_crypt
import ast

from main import app
from modules.bulb import Bulb

# Based on configuration, use a different database.
if app.debug:
    db = SqliteDatabase('app.db')
else:
    db = MySQLDatabase(host="localhost", database="party", user="party", passwd="party")

def db_init():
    db.connect()
    try:
        db.create_tables([User, Device])
        print('Creating tables...')
        if app.debug:
            u = User.create(username='keane', password="")
            u.set_password('root')
            u.admin = True
            u.save()
            Device.create(name='Bulby', category='bulb')
    except OperationalError:
        pass
    db.close()


class DeviceMapper:
    """
    In-memory representation of one or more devices with a relationship
    to the driver module.
    """
    def __init__(self, id, name, category, devices):
        self.id = id
        self.name = name
        self.category = category
        self.devices = devices


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


class Device(BaseModel):
    name = CharField(unique=True)
    category = CharField()
    data = CharField(default='{}')

    def get_object(self):
        if self.category == 'bulb':
            device = Bulb(host=ast.literal_eval(self.data).get('host'))
        return DeviceMapper(self.id, self.name, self.category, device)

