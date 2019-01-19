function enum_virsh() {
    $('.computer').each(function(i, a) {
        ws.emit('enum virsh', {device: a.id});
    });
}
ws.on('vms', function(data) {
    console.log(data);
    var device = $('#' + data.device + '-table');
    $.each(data.vms, function(a, b) {
        console.log(b);
        device.append('<tr><td>' + b[0] + '</td><td>' + b[1] + '</td><td></td></tr>');
    });
});

$('.refresh-vms').click(function(data) {
    enum_virsh();
});

enum_virsh();
setInterval(enum_virsh, 60000);
