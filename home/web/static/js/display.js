var ws = io.connect('//' + document.domain + ':' + location.port);

$('#widgets').hide();
$('#update').hide();
nextbus();
setInterval(nextbus, 30000);
setInterval(presence, 30000);

function nextbus() {
    ws.emit('next bus');
}

function presence() {
    ws.emit('get presence');
}

function nicetime(date) {
    return date.getHours() + ":" + pad2(date.getMinutes());
}

function pad2(number) {
    // https://www.electrictoolbox.com/pad-number-two-digits-javascript/
    return (number < 10 ? '0' : '') + number
}

ws.on('next bus data', function(data) {
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

ws.on('presence data', function(data) {
    alert(data);
});

ws.on('display refresh', function () {
    location.reload();
});

$('#dashboard').click(showWidgets);
$('#dashboard').on("tap", showWidgets);
$('#note').click(showWidgets);
$('#note').on("tap", showWidgets);

var intervalid;
function showWidgets() {
    clearInterval(intervalid);
    $('#dashboard').toggle();
    $('#widgets').toggle();
    intervalid = setInterval(showDash, 5000);
}

function showDash() {
    $('#widgets').hide();
    $('#dashboard').show();
    clearInterval(intervalid);
}

function resetTimer() {
    clearInterval(intervalid);
}

$('body').click(resetTimer);
$('body').on("tap", resetTimer);

var update = false;
ws.on('update', function (data) {
    update = true;
    $('#widgets').hide();
    $('#note').hide();
    $('#dashboard').hide();
    $('#update').show();

});

ws.on('connect', function () {
    if (update) {
        location.reload(true);
    }
});

$(".widget").click(function () {
    ws.emit('widget', {id: this.id});
});
