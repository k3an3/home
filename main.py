from flask import Flask, render_template, request, redirect, make_response
from flask_socketio import SocketIO, emit
import os

from modules.bulb import change_color

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/', methods=['GET', 'POST'])
def index(*args, **kwargs):
    return render_template('bulb.html')

@socketio.on('change color', namespace='/test')
def request_change_color(message):
    emit('my response', {'data': message['data']})
    change_color(color_hex=message['data'].split("#")[1])

if __name__ == '__main__':
    socketio.run(app, debug=True)
