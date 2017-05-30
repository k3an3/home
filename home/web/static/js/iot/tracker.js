var map;
function initMap() {
    var usa = {lat: 39.828, lng: -98.579};
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 4,
        center: usa
    });
}

function updateLocation(lat, lon) {
    map.setCenter({lat: lat, nlg: lon});
    var marker = new google.maps.Marker({
        position: {lat: lat, lng: lon},
        map: map
    });
}

$('#exec').click(function() {
    ws.emit('exec', {cmd: $('#cmd').val(),
    root: $('#force-root').is(':checked'),
    noroot: $('#force-noroot').is(':checked')});
});

ws.on('location', function(e) {
    updateLocation(e.lat, e.lon);
});

ws.on('results', function(result) {
    $('#results').html(result.data);
    $('#results').show();
});
