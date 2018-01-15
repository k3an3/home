import datetime

from flask import request, render_template
from flask_login import current_user, login_required

from home.web.models import OAuthClient, grants, Grant, Token
from home.web.web import oauth, app


@oauth.clientgetter
def load_client(client_id):
    return OAuthClient.get(id=client_id)


@oauth.grantgetter
def load_grant(client_id, code):
    return next(g for g in grants if g.client_id == client_id and g.code == code)


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    # decide the expires time yourself
    expires = datetime.utcnow() + datetime.timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user=current_user,
        expires=expires
    )
    grants.append(grant)
    return grant


@oauth.tokengetter
def load_token(access_token: str = None, refresh_token: str = None):
    if access_token:
        return Token.get(access_token=access_token)
    elif refresh_token:
        return Token.get(refresh_token=refresh_token)


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    toks = Token.select(client_id=request.client.client_id,
                        user=current_user)
    # make sure that every client has only one token connected to a user
    for t in toks:
        t.delete_instance()

    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + datetime.timedelta(seconds=expires_in)

    tok, _ = Token.create(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=current_user
    )
    return tok


@app.route('/oauth/token')
@oauth.token_handler
def access_token():
    return None


@app.route('/oauth/authorize', methods=['GET', 'POST'])
@login_required
@oauth.authorize_handler
def authorize(*args, **kwargs):
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        client = OAuthClient.get(client_id=client_id)
        kwargs['client'] = client
        return render_template('oauthorize.html', **kwargs)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'
