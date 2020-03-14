ws.emit('admin', {
    command: 'refresh logs',
});

ws.emit('admin', {
    command: 'get config',
});

function editDevice() {
    ws.emit('admin', {
        action: 'add',
        id: $('#id').val(),
        name: $('#name').val(),
        category: $('#category').val(),
        data: $('#data').val()
    });
}

$('.visibility ').click(function (e) {
    ws.emit('admin', {
        command: 'visible',
        iface: $(this).attr('id'),
    });
});

$('#refresh_display').click(function () {
    ws.emit('admin', {
        command: 'refresh_display'
    });
});

$('#admin-restart').click(function () {
    ws.emit('admin', {
        command: 'restart'
    });
});

$('#admin-update').click(function () {
    ws.emit('admin', {
        command: 'update'
    });
});

function revoke(name) {
    ws.emit('admin', {command: 'revoke', name: name});
}

function del_user(name) {
    ws.emit('admin', {command: 'delete', name: name});
}

$('#saveconfig').hide();
$('#editconfig').click(function () {
    $('#config').removeAttr('readonly');
    $(this).hide();
    $('#saveconfig').show();
});

$('#saveconfig').click(function () {
    $('#config').attr('readonly', true);
    $(this).hide();
    $('#editconfig').show();
    ws.emit('admin',
        {
            command: 'update config',
            config: $('#config').val()
        }
    );
});

$('#refresh_logs').click(function () {
    ws.emit('admin', {
        command: 'refresh logs',
    });
});

ws.on('logs', function (logs) {
    $('#logs').html(logs);
});

$(".saveperms").click(function () {
    var client = $(this).attr('id');
    client = client.slice(client.indexOf('-') + 1);
    ws.emit('admin',
        {
            command: 'update permissions',
            name: client,
            perms: $('#perms-' + client).val()
        });
});

$(".u_saveperms").click(function () {
    var user = $(this).attr('id');
    user = user.slice(user.indexOf('-') + 1);
    ws.emit('admin',
        {
            command: 'user update permissions',
            name: user,
            perms: $('#u_perms-' + user).val()
        });
});

$(".u_regentok").click(function () {
    let user = $(this).attr('id');
    user = user.slice(user.indexOf('-') + 1);
    ws.emit('admin',
        {
            command: 'user regen token',
            name: user,
        });
});
