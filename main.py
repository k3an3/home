from flask import Flask, render_template, request, redirect, make_response, flash
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_required, login_user
import os

from modules.bulb import change_color

from models import *

app = Flask(__name__)
app.secret_key = '\xff\xe3\x84\xd0\xeb\x05\x1b\x89\x17\xce\xca\xaf\xdb\x8c\x13\xc0\xca\xe4'
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def index(*args, **kwargs):
    return render_template('bulb.html')

@socketio.on('change color', namespace='/test')
def request_change_color(message):
    emit('push color', message['color'], broadcast=True)
    print(message['bright'])
    change_color(color_hex=message['color'].split("#")[1],
                 brightness=message.get('bright', 100))

@login_manager.user_loader
def user_loader(user_id):
    return User.get(username=user_id)

@app.route('/login', methods=['POST'])
def login():
    user = User.get(username=request.form.get('username'))
    if user.password == request.form.get('password'):
        login_user(user)
        flash('Logged in successfully.')
    return redirect('/')

if __name__ == '__main__':
    db_init()
    socketio.run(app, debug=True)
