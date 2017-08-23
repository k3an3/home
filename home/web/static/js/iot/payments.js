$('#add_user').click(function () {
    ws.emit('add payment user', {name: $('#add_username').val(), email: $('#add_email').val()});
});
$('#add_due_submit').click(function () {
    ws.emit('add dues', {amount: $('#add_due').val(), date: $('#add_duedate').val()});
});
ws.emit('get payment data', {});
ws.on('payment data', function (data) {
    $('#users').html(data.users);
    $('#dues').html(data.dues);
});
