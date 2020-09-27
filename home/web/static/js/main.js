/**
 * Created by keane on 2/26/17.
 */

var ws = io.connect('//' + document.domain + ':' + location.port);
var last = "#FFFFFF";
var bright = 100;
var target = "0";

var update = false;
var run_session = $('#run_session').val();

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

ws.on('run session', function (session) {
    if (session !== run_session) {
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
    message(data);
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

$(".widget").click(function () {
    ws.emit('widget', {id: this.id});
});


ws.on('config', function(config) {
    $('#config').html(config);
});

// https://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb
function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

ws.on("device state", function(data) {
    var t = $('#status-' + data.device.replace(' ', '_'));
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

setTimeout(function () {
    $('#messages2').fadeOut();
}, 3000);

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
