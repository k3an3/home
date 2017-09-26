var ws = io.connect('//' + document.domain + ':' + location.port);

$('#widgets').hide();
$('#update').hide();
nextbus();
setInterval(nextbus, 30000);
setInterval(presence, 30000);
$('.btn').addClass('btn-block');
$('.btn-group').removeClass('btn-group');

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
            if (delta >= -1)
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

function showWidgets() {
    $('#dashboard').toggle();
    $('#widgets').toggle();
}

function showDash() {
    $('#widgets').hide();
    $('#dashboard').show();
}

// https://stackoverflow.com/a/4029518
var idleInterval = setInterval(timerIncrement, 6000);
var idleTime = 0;

//Zero the idle timer on mouse movement.
$(this).mousemove(function (e) {
    idleTime = 0;
});

$(this).keypress(function (e) {
    idleTime = 0;
});

$(this).on("tap", function (e) {
    idleTime = 0;
});

function timerIncrement() {
    idleTime += 1;
    if (idleTime > 9) {
        showDash();
        idleTime = 0;
    }
}

// End copy

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

ws.on('reload', function () {
    location.reload();
});

$(".widget").click(function () {
    ws.emit('widget', {id: this.id});
});
