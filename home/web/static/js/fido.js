function register() {
    fetch('/api/user/fido2/register', {
        method: 'POST',
        credentials: 'same-origin',
    }).then(function (response) {
        if (response.ok) return response.arrayBuffer();
        throw new Error('Error getting registration data!');
    }).then(CBOR.decode).then(function (options) {
        return navigator.credentials.create(options);
    }).then(function (attestation) {
        let name = prompt("Enter token name:")
        return fetch('/api/user/fido2/complete?name=' + name, {
            method: 'POST',
            headers: {'Content-Type': 'application/cbor'},

            body: CBOR.encode({
                "attestationObject": new Uint8Array(attestation.response.attestationObject),
                "clientDataJSON": new Uint8Array(attestation.response.clientDataJSON),
            })
        });
    }).then(function (response) {
        let stat = response.ok ? 'successful' : 'unsuccessful';
        alert('Registration ' + stat);
        get_tokens();
    }, function (reason) {
        alert(reason);
    }).then(function () {
    });
}

$("#token_register").click(register);

function delete_fido(id) {
    ws.emit('delete_fido_token', {'id': id});
    $("#row_fido_" + id.toString()).remove();
}

function get_tokens() {
    ws.emit('list_fido_tokens');
    ws.on('tokens_result', function (data) {
        let div = $("#fido_tokens");
        if (data.tokens.length > 0) {
            div.html('');
            data.tokens.forEach(function (token) {
                div.append(`<p id="row_fido_${token.id}">"${token.name}",&nbsp;added ${token.added}&nbsp;-&nbsp;<a href="javascript:void(0)" onclick="delete_fido(${token.id});">Delete</a></p>`);
            });
        }
    });
}

setTimeout(get_tokens, 1000);