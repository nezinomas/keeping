// focus on [autofocus] attribute
$(document).on('shown.bs.modal', '#modal', function () {
    $(this).find('[autofocus]').focus();
});


htmx.on("htmx:afterSwap", (e) => {
    // Response targeting #dialog => show the modal
    if (e.detail.target.id == "dialog") {
        $("#modal").modal("show").draggable({ handle: ".modal-header" });
    }
})


$(document).on('shown.bs.modal', '.modal', function () {
    $(this).find('[autofocus]').focus();
});


htmx.on("htmx:beforeSwap", (e) => {
    if (e.detail.target.id == "dialog" && !e.detail.xhr.response) {
        // find submit button id
        var subbmiter = e.detail.requestConfig.triggeringEvent.submitter.id

        // remove error messages
        $('.invalid-feedback').remove();
        $('.is-invalid').removeClass('is-invalid');

        if(subbmiter == '_new') {
            var price = $('#id_price');
            if (price) {
                price.val('');
            }

            var price_sum_field = $('.sum-prices-field');
            if (price_sum_field) {
                price_sum_field.val('0.0');
            }

            var qty = $('#id_quantity');
            if (qty) {
                qty.val('1');
            }

            var title = $('#id_title');
            if (title) {
                title.val('');
            }

            var remark = $('#id_remark');
            if (remark) {
                remark.val('');
            }

            var exception = $('#id_exception');
            if (exception) {
                exception.prop('checked', false);
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
    var form = $('.form');
    var trigger_name = form.attr("data-hx-trigger-form");
    var data_inserted = form.attr('data-hx-inserted');

    alert(`Trigger: ${trigger_name} type: ${typeof (trigger_name)} | insert: ${data_inserted} type: ${typeof (data_inserted)}`);

    if (trigger_name === 'None' || trigger_name == undefined) return;

    if (trigger_name && data_inserted) {
        alert('Triggering event');
        htmx.trigger("body", trigger_name, {});
    }
});
