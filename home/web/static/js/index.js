/**
 * Created by keane on 2/26/17.
 */
$('.nav a').click(function (e) {
    e.preventDefault();
    updateTarget($(this).context.hash.split('#')[1]);
    $(this).tab('show');
});

function updateTarget(newTarget) {
    target = newTarget;
}