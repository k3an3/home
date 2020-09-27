/**
 * Created by keane on 2/26/17.
 */
$('#logout').click(function () {
    document.location = '/logout';
});

$('.tab a').click(function (e) {
    e.preventDefault();
    updateTarget($(this).context.hash.split('#')[1]);
    $(this).tab('show');
});

$('#homea').click(function () {
    $('.navbar-nav li').each(function () {
        $(this).removeClass('active');
    });
});

$('#messages').hide();
function message(data) {
    $('#messages').attr('class', 'alert floating-message');
    $('#messages').html(data.content);
    $("#messages").css('visibility', 'visible');
    $('#messages').addClass(data.class);
    $('#messages').fadeIn();
    setTimeout(function () {
        $('#messages').fadeOut();
    }, 5000);
}

function updateTarget(newTarget) {
    target = newTarget;
    $('#' + target).trigger("click");
}

$('#login-form').submit(function(e) {
    e.preventDefault();

    let headers = new Headers();
    headers.set('Accept', 'application/json');
    let form_data = new URLSearchParams([...new FormData(e.target).entries()])
    fetch("/user/login", {
        method: "POST",
        headers: headers,
        body: form_data,
        credentials: "same-origin",
    }).then(function(response) {
        return response.json();
    }).then(function(data) {
        if (data.result == "err")
            message({content: data.msg, class: "alert-danger"});
        else if (data.result == "fido2") {
            message({content: data.msg, class: "alert-success"});
            authenticate();
        } else {
            window.location = "/";
        }
    });

});
