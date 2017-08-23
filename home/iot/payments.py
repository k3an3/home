from flask_socketio import emit
from peewee import MySQLDatabase, SqliteDatabase, OperationalError, Model, CharField, DecimalField

from home import settings
from home.iot.mail import Mail
from home.web.utils import ws_login_required
from home.web.web import socketio

if True:
    db = SqliteDatabase('pay.db')
else:
    db = MySQLDatabase(host="localhost", database="pay", user="pay", passwd="pay")

mail_handler = None

BODY = """Hello {},

The latest payment for your apartment has been finalized. The amount in full is ${}. Please pay this amount to {} before {}. For more details on the payment breakdown and other dues, see {}. 

Thank you for doing business with us.
"""


def db_init():
    db.connect()
    try:
        db.create_tables([Payment, Due, User])
    except OperationalError:
        pass
    db.close()


@socketio.on('add dues')
@ws_login_required
def dues(due):
    if float(due['amount']) > 0:
        d = Due.create(amount=due['amount'], date=due['date'])
        try:
            for user in User.select():
                mail_handler.send_email("105 Westwood Payment " + d.date, user.email, settings.MAIL_FROM,
                                        BODY.format(user.name, d.amount, settings.PAY_TO, d.date,
                                                    settings.PAYMENT_SPREADSHEET))
        except Exception:
            emit("payment sent", "There was an error sending the email(s).")
        else:
            emit("payment sent", "Success")



@socketio.on('add payment user')
@ws_login_required
def adduser(user):
    User.create(name=user['name'], email=user['email'])


@socketio.on('get payment data')
@ws_login_required
def pay_data(empty):
    emit('payment data', {'users': [u.email + '\n' for u in User.select()],
                          'dues': [('$' + str(d.amount), d.date + '\n') for d in Due.select()]})


class Payments:
    def __init__(self):
        db_init()
        global mail_handler
        mail_handler = Mail(settings.SMTP_SERVER, settings.SMTP_PORT, settings.SMTP_USERNAME, settings.SMTP_PASSWORD)


class BaseModel(Model):
    class Meta:
        database = db


class Payment(BaseModel):
    pass


class Due(BaseModel):
    amount = DecimalField()
    date = CharField()


class User(BaseModel):
    name = CharField()
    email = CharField()
