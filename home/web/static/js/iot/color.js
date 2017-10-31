/**
 * Created by keane on 2/26/17.
 */
function mouseOverColor(hex) {
    console.log(target);
    ws.emit('change color', {color: hex, bright: bright, device: target});
    $("#preview").css('background-color', hex);
    $("#preview").css('visibility', 'visible');
    $("#hex").val(hex);
    return false;
}

function clickColor(hex) {
    mouseOverColor(hex);
    last = hex;
    return false;
}

function updateColor() {
    mouseOverColor($("#hex").val());
    last = $("#hex").val();
    return false;
}

function mouseOutMap() {
    ws.emit('change color', {color: last, bright: bright, device: target});
    ws.emit('outmap', {color: last, bright: bright, device: target});
    $("#hex").val(last);
    $("#preview").css('visibility', 'hidden');
    return false;
}

function changeState() {
    ws.emit('change state');
}

ws.on('push color', function (data) {
    console.log(data.device == target);
    if (data.device == target) {
        $("#preview" + target).css('background-color', data.color);
        $("#preview" + target).css('visibility', 'visible');
        $("#hex" + target).val(data.color);
    }
});

function changewhite(val) {
    ws.emit('change color', {color: "000000", white: val, bright: bright, device: target});
}