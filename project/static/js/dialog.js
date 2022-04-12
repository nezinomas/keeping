$(document).keydown(function (event) {
    if (event.keyCode == 27) {
        $('#modal-form').modal("hide");
    }
});


// replace dot in year field
$(document).ready(function () {
    var fields = ['year', 'closed', 'valid_for'];
    var len = fields.length;
    for (i = 0; i < len; i++) {
        var field = fields[i];
        var year = $(`#id_${field}:text`).attr('value')
        if (year) {
            year = year.replace(".", "");
            year = year.replace(",", "");

            $(`#id_${field}`).attr('value', year);
            $(`#id_${field}:text`).val(year);
        }
    }
});

// eh?
// $(document).on('submit', '.js_form', function (e) {
//     e.preventDefault();
// });


// HTMX related functions

htmx.on("htmx:afterSwap", (e) => {
    // Response targeting #dialog => show the modal
    if (e.detail.target.id == "dialog") {
        $("#modal").modal("show").draggable({ handle: ".modal-header" });
    }
})


htmx.on("htmx:beforeSwap", (e) => {
    if (e.detail.target.id == "dialog" && !e.detail.xhr.response) {
        // find submit button id
        var subbmiter = e.detail.requestConfig.triggeringEvent.submitter.id

        // remove error messages
        $('.invalid-feedback').remove();
        $('.is-invalid').removeClass('is-invalid');

        if(subbmiter == '_new') {
            $('#modal form')[0].reset();
        }

        if(subbmiter == '_close') {
            $('#modal').modal('hide');
            $('#modal form')[0].reset();
        }
        e.detail.shouldSwap = false;
    }
})
