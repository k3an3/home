var ws = io.connect('//' + document.domain + ':' + location.port);

$('#widgets').hide();
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

$('body').click(showWidgets);
$('body').on("tap", showWidgets);

var intervalid;
function showWidgets() {
    clearInterval(intervalid);
    $('#dashboard').fadeToggle();
    $('#widgets').fadeToggle();
    intervalid = setInterval(showDash, 60000);
}

function showDash() {
    $('#widgets').fadeOut("slow", function() {});
    $('#dashboard').fadeIn();
    clearInterval(intervalid);
}
