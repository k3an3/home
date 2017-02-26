from flask import abort
from flask import request, flash, redirect, url_for
from flask_login import current_user, login_user, fresh_login_required, login_required, logout_user

from home.web.models import User, APIClient
from home.web.utils import ws_login_required
from home.web.web import app, socketio


@app.route('/login', methods=['POST'])
def login():
    user = User.get(username=request.form.get('username'))
    if user.check_password(request.form.get('password')):
        login_user(user)
        flash('Logged in successfully.')
    return redirect(url_for('index'))


@app.route("/user/password", methods=['POST'])
@fresh_login_required
@login_required
def change_password():
    if current_user.admin:
        user = User.get(username=request.form.get('username'))
    elif current_user.check_password(request.form.get('password')):
        user = current_user
    if request.form.get('new_password') == request.form.get('new_password_confirm'):
        user.set_password(request.form.get('new_password'))
        user.save()
    return redirect(url_for('index'))


@app.route("/user/create", methods=['POST'])
@fresh_login_required
@login_required
def create_user():
    if not current_user.admin:
        abort(403)
    if request.form.get('api'):
        APIClient.create(name=request.form.get('username'))
    else:
        if len(request.form.get('password')):
            u = User.create(username=request.form.get('username'),
                            password="")
            u.set_password(request.form.get('password'))
            u.admin = request.form.get('admin')
            u.save()
        else:
            abort(500)
    return redirect(url_for('index'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@socketio.on('revoke', namespace='/ws')
@ws_login_required
def revoke(message):
    client = APIClient.get(name=message.get('name'))
    client.delete_instance()
