$('#showimages').click(toggle_streams);
$('#showrecs').click(toggle_recordings);
$('#next').click(next_page);
$('#prev').click(prev_page);
var streams_visible = false;
var recordings_visible = false;
var page = 6;

ws.on('push video', function(data) {
    $("#monitor").html('');
    data.feeds.forEach(function(e) {
        $('#monitor').append('<img class="feed img-responsive" style="float:left;width:50%;" data-src="/security/stream/' + e + '/" title="' + e + '">')
    });
    $("#recordings").html('');
    for (var key in data.recordings) {
        data.recordings[key].forEach(function(e) {
            $('#recordings').append('<a target="_blank" href="/security/recordings/' + key + '/' + e + '"><video type="video/mp4" style="float:left;width:30%;margin 0 auto;" src="/security/recordings/' + key + '/' + e + '" title="' + e + '"autoplay loop></video></a>');
        });
    }
    if (streams_visible)
        reveal_stream();
});

function next_page() {
    page += 6;
    ws.emit('get video', page);
}

function prev_page() {
    if (page >= 12) {
        page -= 6;
        ws.emit('get video', page);
    }
}

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
    $("#pager").show();
    recordings_visible = true;
}

function hide_recs() {
    $("#recordings").hide();
    $("#recordings").html('');
    $("#pager").hide();
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
        button.removeAttr('class');
        button.addClass('btn btn-warning');
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
