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
    emit('push color', message['color'], broadcast=True)
    print(message['bright'])
    change_color(color_hex=message['color'].split("#")[1],
                 brightness=message.get('bright', 100))

if __name__ == '__main__':
    socketio.run(app, debug=True)
