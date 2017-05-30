var map;
//noinspection JSUnusedGlobalSymbols
function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 3,
        center: {lat: 39.828, lng: -98.579}
    });
}
setTimeout(function(){ initMap(); }, 2000);

function updateLocation(lat, lon) {
    map.setCenter({lat: lat, lng: lon});
    map.setZoom(15);
    var marker = new google.maps.Marker({
        position: {lat: lat, lng: lon},
        map: map
    });
}

function exec() {
    ws.emit('exec', {
        cmd: $('#cmd').val(),
        root: $('#force-root').is(':checked'),
        noroot: $('#force-noroot').is(':checked')
    });
}

$('#exec').click(exec);

$('#locate').click(function() {
});

ws.on('location', function(e) {
    updateLocation(e.lat, e.lon);
});

ws.on('results', function(result) {
    $('#result-body').html(result.data);
    $('#results').show();
});

ws.on('android_connection', function(data) {
    if (data.state == 'connected') {
        $('#android-status').html('Connected');
        $('#android-status').attr('style', 'color: green;');
    } else if (data.android-status == 'disconnected') {
        $('#android-status').html('Disconnected');
        $('#android-status').attr('style', 'color: red;');
    }
});

$("#cmd").keyup(function(e) {
    // 13 is ENTER
    if (e.which === 13)
        exec();
});
