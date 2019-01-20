var status_label = {running: 'success', 'shut off': 'danger'};
function enum_virsh() {
    $('.computer').each(function(i, a) {
        ws.emit('enum virsh', {device: a.id});
    });
}

function buttons(device) {
    var btn = '<div class="btn-group" role="group">';
    btn += '<button id="{}-start" type="button" class="btn btn-sm btn-success vm-control">Start</button>';
    btn += '<button id="{}-shutdown" type="button" class="btn btn-sm btn-danger vm-control">Stop</button>';
    btn += '<button id="{}-restart" type="button" class="btn btn-sm btn-warning vm-control">Restart</button>';
    btn += '</div>';
    return btn.replace(/{}/g, device);
}

$('body').on('click', 'button.vm-control', function(a) {
    var s = a.target.id.split('-');
    ws.emit('vm ctrl', {
        device: s[0],
        vm: s[1],
        action: s[2]
    });
    setInterval(enum_virsh, 5000);
    setInterval(enum_virsh, 10000);
});

ws.on('vms', function(data) {
    var device = $('#' + data.device + '-table');
    device.html('');
    $.each(data.vms, function(a, b) {
        var status = '<span class="label label-' + status_label[b[1]] + '">' + b[1] + '</span>';
        device.append('<tr><td>' + b[0] + '</td><td>' + status + '</td><td>' + buttons(data.device + '-' + b[0]) + '</td></tr>');
    });
});

$('.refresh-vms').click(function() {
    enum_virsh();
    message({content: 'Refreshing...', class: 'alert-info'});
});

enum_virsh();
setInterval(enum_virsh, 60000);
