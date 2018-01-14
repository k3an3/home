/**
 * Created by keane on 2/26/17.
 */

var ws = io.connect('//' + document.domain + ':' + location.port);
var last = "#FFFFFF";
var bright = 100;
var target = "0";
$('#messages').hide();

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
    });
});

$('#refresh_display').click(function() {
    ws.emit('admin', {
        command: 'refresh_display'
    });
});

function revoke(name) {
    ws.emit('admin', {command: 'revoke', name: name});
}

var update = false;

ws.on('disconnect', function () {
    $('#status').html('Status: <span style="color:red">Disconnected</span>');
});

ws.on('connect', function () {
    $('#status').html('Status: <span style="color:green">Connected</span>');
    $("#loadingScreen").dialog('close');
    if (update) {
        location.reload(true);
    }
});

ws.on('preview reset', function (msg) {
    $("#hex").val(msg);
    $("#preview").css('visibility', 'hidden');
});

$('#logout').click(function () {
    document.location = "/logout";
});

ws.on('message', function (data) {
    $('#messages').attr('class', 'alert floating-message');
    $('#messages').html(data.content);
    $("#messages").css('visibility', 'visible');
    $('#messages').addClass(data.class);
    $('#messages').fadeIn();
    setTimeout(function () {
        $('#messages').fadeOut();
    }, 5000);
});

ws.on('event', function (data) {
    var table = $('#events');
});

$("#loadingScreen").dialog({
    autoOpen: false,    // set this to false so we can manually open it
    dialogClass: "loadingScreenWindow",
    closeOnEscape: false,
    draggable: false,
    width: 460,
    minHeight: 50,
    modal: true,
    buttons: {},
    resizable: false,
    open: function() {
        // scrollbar fix for IE
        $('body').css('overflow','hidden');
    },
    close: function() {
        // reset overflow
        $('body').css('overflow','auto');
    }
}); // end of dialog

ws.on('update', function (data) {
    update = true;
    waitingDialog({title: 'Updating...'})
});

ws.on('reload', function () {
    location.reload();
});

function waitingDialog(waiting) {
    $("#loadingScreen").html(waiting.message && '' != waiting.message ? waiting.message : 'Please wait...');
    $("#loadingScreen").dialog('option', 'title', waiting.title && '' != waiting.title ? waiting.title : 'Loading');
    $("#loadingScreen").dialog('open');
}

$('#saveconfig').hide();
$('#editconfig').click(function() {
    $('#config').removeAttr('readonly');
    $(this).hide();
    $('#saveconfig').show();
});

$('#saveconfig').click(function() {
    ws.emit('admin',
        {
            command: 'update config',
            config: $('#config').val()
        }
    );
});

$(".widget").click(function () {
    ws.emit('widget', {id: this.id});
});

$('#refresh_logs').click(function() {
    ws.emit('admin', {
        command: 'refresh logs',
    });
});

ws.on('logs', function(logs) {
    $('#logs').html(logs);
});

ws.on('config', function(config) {
    $('#config').html(config);
});

$(".device-status").each(function() {
    ws.emit('device state', {'device': this.id.split('-')[1].replace('_', ' ')});
});

// https://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb
function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

ws.on("device state", function(data) {
    var t = $('#status-' + data.device.replace(' ', '_'));
    console.log(data);
    if (data.state != null && typeof data.state === 'object') {
        var colors = data.state;
        if (colors.white != 0)
            t.html('on');
        else
            t.html('<div class="color-box" style="background-color: ' + rgbToHex(colors.red, colors.green, colors.blue)+ ';"></div>');
    }
    else
        t.html(data.state);
});


$(".saveperms").click(function() {
    var client = $(this).attr('id').split('-')[1];
    ws.emit('admin',
        {
            command: 'update permissions',
            name: client,
            perms: $('#perms-' + client).val()
        });
});


ws.emit('admin', {
    command: 'refresh logs',
});

ws.emit('admin', {
    command: 'get config',
});

setTimeout(function () {
    $('#messages2').fadeOut();
}, 3000);