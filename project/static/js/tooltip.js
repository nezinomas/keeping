
function setUpToolTip() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

/*
    wait 3000ms for ajax calls to finish
    only then load setup tooltip script
*/
$.holdReady(true);
setTimeout(function () {
    $.holdReady(false);
}, 3000);

$(document).ready(function () {
    setUpToolTip();
});


/* initializate the tooltips after model hide */
$(document).on('hidden.bs.modal', '#modal', function () {
    alert('o cia')
    setUpToolTip();
})
