import re

from fido2 import cbor
from fido2.client import ClientData
from fido2.ctap2 import AttestationObject, AuthenticatorData, AttestedCredentialData
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity
from flask import request, session
from flask_login import current_user, login_required, login_user
from flask_socketio import emit
from peewee import DoesNotExist

from home.settings import BASE_URL
from home.web import app, send_message, socketio, ws_login_required
from home.web.models import FIDOToken, User

rp = PublicKeyCredentialRpEntity(
    re.match(r'https?:\/\/([a-zA-Z0-9.-]+)(?::[0-9]{1,5})?\/.*', BASE_URL)[1],
    "Home server")
server = Fido2Server(rp)


def get_all_tokens(user):
    return [AttestedCredentialData(token.data) for token in user.fido_tokens]

@app.route("/api/user/fido2/register", methods=["POST"])
@login_required
def register_begin():
    registration_data, state = server.register_begin(
        {
            "id": str(current_user.id).encode(),
            "name": current_user.username,
            "displayName": current_user.username,
        },
        get_all_tokens(current_user),
        user_verification="discouraged",
        authenticator_attachment="cross-platform"
    )
    print(state)
    session["state"] = state
    print("\n\n\n\n")
    print(registration_data)
    print("\n\n\n\n")
    return cbor.encode(registration_data)


@app.route("/api/user/fido2/complete", methods=["POST"])
@login_required
def register_complete():
    data = cbor.decode(request.get_data())
    client_data = ClientData(data["clientDataJSON"])
    att_obj = AttestationObject(data["attestationObject"])
    print("clientData", client_data)
    print("AttestationObject:", att_obj)

    auth_data = server.register_complete(session["state"], client_data, att_obj)

    FIDOToken.create(user=current_user.id,
                     name=request.args["name"],
                     data=auth_data.credential_data)
    print("REGISTERED CREDENTIAL:", auth_data.credential_data)
    return cbor.encode({"status": "OK"})


@socketio.on('list_fido_tokens')
@ws_login_required
def list_fido():
    emit('tokens_result', {'tokens': [t.to_dict() for t in current_user.fido_tokens]})


@socketio.on('delete_fido_token')
@ws_login_required
def delete_fido(data):
    try:
        FIDOToken.get(user=current_user.id, id=data['id']).delete_instance();
    except DoesNotExist:
        send_message("Invalid FIDO token!", 'error')
    else:
        send_message("Deleted FIDO token successfully!", 'success')


@app.route("/api/user/fido2/auth/start", methods=["POST"])
def authenticate_begin():
    user = User.get(session['fido_preauth_user'])
    auth_data, state = server.authenticate_begin(get_all_tokens(user))
    session["state"] = state
    return cbor.encode(auth_data)


@app.route("/api/user/fido2/auth/finish", methods=["POST"])
def authenticate_complete():
    data = cbor.decode(request.get_data())
    credential_id = data["credentialId"]
    client_data = ClientData(data["clientDataJSON"])
    auth_data = AuthenticatorData(data["authenticatorData"])
    signature = data["signature"]
    user = User.get(session["fido_preauth_user"])
    print("clientData", client_data)
    print("AuthenticatorData", auth_data)

    server.authenticate_complete(
        session.pop("state"),
        get_all_tokens(user),
        credential_id,
        client_data,
        auth_data,
        signature,
    )
    print("ASSERTION OK")
    login_user(user)
    return cbor.encode({"status": "OK"})
