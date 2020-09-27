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


function authenticate() {
    fetch('/api/user/fido2/auth/start', {
      method: 'POST',
    }).then(function(response) {
      if(response.ok) return response.arrayBuffer();
      throw new Error('No credential available to authenticate!');
    }).then(CBOR.decode).then(function(options) {
      return navigator.credentials.get(options);
    }).then(function(assertion) {
      return fetch('/api/user/fido2/auth/finish', {
        method: 'POST',
        headers: {'Content-Type': 'application/cbor'},
        body: CBOR.encode({
          "credentialId": new Uint8Array(assertion.rawId),
          "authenticatorData": new Uint8Array(assertion.response.authenticatorData),
          "clientDataJSON": new Uint8Array(assertion.response.clientDataJSON),
          "signature": new Uint8Array(assertion.response.signature)
        })
      })
    }).then(function(response) {
      let stat = response.ok ? 'successful' : 'unsuccessful';
      alert('Authentication ' + stat);
    }, function(reason) {
      alert(reason);
    }).then(function() {
      window.location = '/';
    });
}
