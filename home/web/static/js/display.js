var ws = io.connect('//' + document.domain + ':' + location.port);

nextbus();
setInterval(nextbus, 30000);

function nextbus() {
    ws.emit('next bus');
}

function nicetime(date) {
    return date.getHours() + ":" + pad2(date.getMinutes());
}

function pad2(number) {
    // https://www.electrictoolbox.com/pad-number-two-digits-javascript/
    return (number < 10 ? '0' : '') + number
}

ws.on('next bus data', function (data) {
    var nbd = $('#nextbusdata');
    nbd.html('');
    data.forEach(function (a) {
        nbd.append('<h3>' + a[0] + '</h3>');
        a[1].forEach(function (b) {
            var d = new Date(0);
            d.setUTCMilliseconds(b);
            var delta = d - new Date();
            nbd.append('<p>' + Math.floor(delta / 60000) + " minutes (" + nicetime(d) + ')</p>');
        });
    });
});

ws.on('display refresh', function () {
    location.reload();
});