$(document).keydown(function (event) {
    if (event.keyCode == 27) {
        $('#modal').modal("hide");
    }
});


$(document).on('submit', '.js-form', function (e) {
    e.preventDefault();
});


/* focus on [autofocus] attribute */
$(document).on('shown.bs.modal', '#modal', function () {
    $(this).find('[autofocus]').focus();
});


htmx.on("htmx:afterSwap", (e) => {
    /* Response targeting #dialog => show the modal */
    if (e.detail.target.id == "dialog") {
        $("#modal").modal("show").draggable({ handle: ".modal-header" });
    }
})


htmx.on("htmx:beforeSwap", (e) => {
    if (e.detail.target.id == "dialog" && !e.detail.xhr.response) {
        /* find submit button id */
        let subbmiter = e.detail.requestConfig.triggeringEvent.submitter.id;

        /* remove error messages */
        $('.invalid-feedback').remove();
        $('.is-invalid').removeClass('is-invalid');

        if(subbmiter == '_new') {
            // reset fields values after submit
            let fields = ["price", "fee", "quantity", "title", "remark", "attachment"];
            for (let i in fields) {
                let field = $(`#id_${fields[i]}`);
                if(field) {
                    field.val('');
                }
            }
        }

        if(subbmiter == '_close') {
            $('#modal').modal('hide');
            $('#modal form')[0].reset();
        }

        e.detail.shouldSwap = false;
    }
})


$(document).on('hidden.bs.modal', '#modal', function () {
    let form = $('.form');
    let trigger_name = form.attr("data-hx-trigger-form");
    let data_inserted = form.attr('data-hx-inserted');

    if (trigger_name === 'None' || trigger_name == undefined) {
        return;
    }

    if(trigger_name && data_inserted) {
        htmx.trigger("body", trigger_name, { });
    }
});
