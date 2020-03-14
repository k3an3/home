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

function updateTarget(newTarget) {
    target = newTarget;
    $('#' + target).trigger("click");
}