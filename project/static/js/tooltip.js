
function setUpToolTip() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}


/* initializate the tooltips after model hide */
$(document).on('hidden.bs.modal', '#modal', function () {
    setUpToolTip();
})
