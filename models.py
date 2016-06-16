from peewee import *
from passlib.hash import sha256_crypt

#db = MySQLDatabase(host="localhost", database="party", user="party", passwd="party")
db = SqliteDatabase('app.db')

def db_init():
    db.connect()
    try:
        db.create_tables([User])
        print('Creating tables...')
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
