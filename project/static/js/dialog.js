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
        var subbmiter = e.detail.requestConfig.triggeringEvent.submitter.id;

        /* remove error messages */
        $('.invalid-feedback').remove();
        $('.is-invalid').removeClass('is-invalid');

        if(subbmiter == '_new') {
            const price = $('#id_price');
            const qty = $('#id_quantity');
            const title = $('#id_title');
            const remark = $('#id_remark');
            const exception = $('#id_exception');

            if (price) price.val('0.0');

            if (qty) qty.val('1');

            if (title) title.val('');

            if (remark) remark.val('');

            if (exception) exception.prop('checked', false);
        }

        if(subbmiter == '_close') {
            $('#modal').modal('hide');
            $('#modal form')[0].reset();
        }

        e.detail.shouldSwap = false;
    }
})


$(document).on('hidden.bs.modal', '#modal', function () {
    var form = $('.form');
    var trigger_name = form.attr("data-hx-trigger-form");
    var data_inserted = form.attr('data-hx-inserted');

    if (trigger_name === 'None' || trigger_name == undefined) return;

    if(trigger_name && data_inserted) {
        htmx.trigger("body", trigger_name, { });
    }
});
