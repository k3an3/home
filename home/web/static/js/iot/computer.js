let status_label = {running: 'success', 'shut off': 'danger', 'paused': 'info'};

function enum_virsh() {
    $('.computer').each(function(i, a) {
        ws.emit('enum virsh', {device: a.id});
    });
}

function buttons(device) {
    let btn = '<div class="btn-group" role="group">';
    btn += '<button id="{}:start" type="button" class="btn btn-sm btn-success vm-control">Start</button>';
    btn += '<button id="{}:shutdown" type="button" class="btn btn-sm btn-danger vm-control">Stop</button>';
    btn += '<button id="{}:restart" type="button" class="btn btn-sm btn-warning vm-control">Restart</button>';
    btn += '<button id="{}:save" type="button" class="btn btn-sm btn-primary vm-control">Save</button>';
    btn += '<button id="{}:restore" type="button" class="btn btn-sm btn-info vm-control">Restore</button>';
    btn += '<button id="{}:suspend" type="button" class="btn btn-sm btn-default vm-control">Pause</button>';
    btn += '<button id="{}:suspend" type="button" class="btn btn-sm btn-primary vm-control">Resume</button>';
    btn += '</div>';
    return btn.replace(/{}/g, device);
}

$('body').on('click', 'button.vm-control', function(a) {
    let s = a.target.id.split(':');
    ws.emit('vm ctrl', {
        device: s[0],
        vm: s[1],
        action: s[2]
    });
    setInterval(enum_virsh, 3000);
    setInterval(enum_virsh, 5000);
});

ws.on('vms', function(data) {
    let device = $('#' + data.device + '-table');
    device.html('');
    $.each(data.vms, function(a, b) {
        let status = '<span class="label label-' + status_label[b[1]] + '">' + b[1] + '</span>';
        device.append('<tr><td>' + b[0] + '</td><td>' + status + '</td><td>' + buttons(data.device + ':' + b[0]) + '</td></tr>');
    });
});

$('.refresh-vms').click(function() {
    enum_virsh();
    message({content: 'Refreshing...', class: 'alert-info'});
});

enum_virsh();
setInterval(enum_virsh, 15000);
