$(document).ready(function () {
    setUpToolTip();
});

function setUpToolTip() {
    var e = $('body').tooltip({selector: '[data-bs-toggle="tooltip"]'});
    e.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    })
}
