
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
