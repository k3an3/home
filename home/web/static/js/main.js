/**
 * Created by keane on 2/26/17.
 */

var ws = io.connect('//' + document.domain + ':' + location.port + '/ws');
var last = "#FFFFFF";
var bright = 100;
var target = "0";

function editDevice() {
    ws.emit('admin', {
        action: 'add',
        id: $('#id').val(),
        name: $('#name').val(),
        category: $('#category').val(),
        data: $('#data').val()
    });
}

$('.visibility ').click(function(e) {
    ws.emit('admin', {
        command: 'visible',
        iface: $(this).attr('id'),
    })
})

function revoke(name) {
    ws.emit('admin', {command: 'revoke', name: name});
}

ws.on('disconnect', function () {
    $('#status').html('Status: <span style="color:red">Disconnected</span>');
});

ws.on('connect', function () {
    $('#status').html('Status: <span style="color:green">Connected</span>');
});

ws.on('preview reset', function (msg) {
    $("#hex").val(msg);
    $("#preview").css('visibility', 'hidden');
});

$('#logout').click(function () {
    document.location = "/logout";
});

ws.on('message', function (data) {
    $('#messages').html(data);
    $("#messages").css('visibility', 'visible');
    $('#messages').fadeIn();
    alert("Please refresh to update devices.")
});

ws.on('event', function (data) {
    var table = $('#events');
});

ws.on('update', function (data) {
    document.location = "/";
});

ws.on('state change', function (data) {
    var bg;
    var color;
    var state = $('#state');
    var button = $('#statusbutton');

    if (data.state == 'alert') {
        bg = 'red';
        color = 'white';
        state.html('alert');
        button.html('Clear');
        button.removeAttr('class').addClass('btn btn-warning');
    } else if (data.state == 'armed') {
        bg = 'green';
        color = 'white';
        state.html('armed');
        button.html('Disable');
        button.removeAttr('class').addClass('btn btn-danger');
    } else {
        bg = '';
        color = 'black';
        state.html('disabled');
        button.html('Enable');
        button.removeAttr('class').addClass('btn btn-success');
    }
    $('.jumbotron').css('background-color', bg);
    $('.jumbotron').css('color', color);
    if (data.message != "")
        $('#warning').html(data.message);
});

setTimeout(function () {
    $('#messages').fadeOut();
}, 3000);