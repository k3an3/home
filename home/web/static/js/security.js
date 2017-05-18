$('#showimages').click(toggle_streams);
$('#showrecs').click(toggle_recordings);
var streams_visible = false;
var recordings_visible = false;

ws.on('push video', function(data) {
    data.feeds.forEach(function(e) {
        $('#monitor').append('<img class="feed img-responsive" style="float:left;width:50%;" data-src="/security/stream/' + e + '/" title="' + e + '">')
    });
    data.recordings.forEach(function(e) {
        $('#recordings').append('<a target="_blank" href="/security/recordings/' + e + '"><video type="video/mp4" style="float:left;width:30%;margin 0 auto;" src="/security/recordings/' + e + '" title="' + e + '"autoplay loop></video></a>');
    });
    if (streams_visible)
        reveal_stream();
});

function toggle_streams() {
    if (streams_visible) {
        hide_stream();
    }
    else {
        ws.emit('get video');
        reveal_stream();
    }
}

function toggle_recordings() {
    if (recordings_visible) {
        hide_recs();
    }
    else {
        ws.emit('get video');
        reveal_recs();
    }
}

function reveal_recs() {
    $("#recordings").show();
    recordings_visible = true;
}

function hide_recs() {
    $("#recordings").hide();
    $("#recordings").html('');
    recordings_visible = false;
}

function reveal_stream() {
    $('.feed').each(function () {
        $(this).attr("src", $(this).attr("data-src"));
    });
    $("#monitor").show();
    streams_visible = true;
}

function hide_stream() {
    $("#monitor").hide();
    $("#monitor").html('');
    streams_visible = false;
}
