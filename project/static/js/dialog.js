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
            var price = document.getElementById("id_price");
            if (price) {
                price.value = '';
            }

            var qty = document.getElementById("id_quantity");
            if (qty) {
                qty.value = '1';
            }

            var title = document.getElementById("id_title");
            if (title) {
                title.value = ''
            }

            var remark = document.getElementById("id_remark");
            if (remark) {
                remark.value = ''
            }

            var exception = document.getElementById("id_exception");
            if (exception) {
                exception.checked = false;
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
    var action = form.attr("data-hx-trigger-form");
    var inserted = form.attr('data-hx-inserted');

    if(action && inserted) {
        htmx.trigger("body", action, { });
    }

});
