import re

from fido2 import cbor
from fido2.client import ClientData
from fido2.ctap2 import AttestationObject
from fido2.server import U2FFido2Server, Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity
from flask import request, session, render_template
from flask_login import current_user, login_required

from home.settings import BASE_URL
from home.web import app, send_message
from home.web.models import FIDOToken


rp = PublicKeyCredentialRpEntity(
    re.match(r'https?:\/\/([a-zA-Z0-9.-]+)(?::[0-9]{1,5})?\/.*', BASE_URL)[1],
    "Home server")
server = Fido2Server(rp)


@app.route("/user/fido2/register")
@login_required
def register_fido():
    return render_template('fido/register.html')


@app.route("/api/user/fido2/register", methods=["POST"])
@login_required
def register_begin():
    registration_data, state = server.register_begin(
        {
            "id": str(current_user.id).encode(),
            "name": current_user.username,
            "displayName": current_user.username,
        },
        [token.data for token in current_user.fido_tokens],
        user_verification="discouraged",
        authenticator_attachment="cross-platform"
    )
    print(state)
    session["state"] = state
    session["tok_name"] = request.form.get("token_name", "Unknown")
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

    new_token = FIDOToken.create(user=current_user.id,
                                 name=session["tok_name"],
                                 data=auth_data.credential_data)
    print("REGISTERED CREDENTIAL:", auth_data.credential_data)
    return cbor.encode({"status": "OK"})

@app.route("/api/authenticate/begin", methods=["POST"])
def authenticate_begin():
    if not credentials:
        abort(404)

    auth_data, state = server.authenticate_begin(credentials)
    session["state"] = state
    return cbor.encode(auth_data)


@app.route("/api/authenticate/complete", methods=["POST"])
def authenticate_complete():
    if not credentials:
        abort(404)

    data = cbor.decode(request.get_data())
    credential_id = data["credentialId"]
    client_data = ClientData(data["clientDataJSON"])
    auth_data = AuthenticatorData(data["authenticatorData"])
    signature = data["signature"]
    print("clientData", client_data)
    print("AuthenticatorData", auth_data)

    server.authenticate_complete(
        session.pop("state"),
        credentials,
        credential_id,
        client_data,
        auth_data,
        signature,
    )
    print("ASSERTION OK")
    return cbor.encode({"status": "OK"})
