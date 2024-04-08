// prevent default form submission
$(document).on('submit', '.modal-form', function (e) {
    e.preventDefault();
});


// focus on [autofocus] attribute
$(document).on('shown.bs.modal', '#modal', function () {
    $(this).find('[autofocus]').focus();
});


// close modal on Close Buton
$(document).on('click', '.modal-close', function (e) {
    modal_hide();
});


// close modal on ESC
$(document).keydown(function (event) {
    if (event.keyCode == 27) {
        modal_hide();
    }
});


// close modal on outside click
window.onclick = function(event) {
    if (event.target == modal) {
        modal_hide();
    }
}


// show modal on click button with hx-target="#dialog"
htmx.on("htmx:afterSwap", (e) => {
    console.log(e.detail.target.id);
    if (e.detail.target.id == "dialog") {
        $('#modal').show();
    }
})


// reload modal form with error messages or reset fields and close modal form
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
            modal_hide();


            $('#modal form')[0].reset();
        }

        e.detail.shouldSwap = false;
    }
})


// trigger htmx on form submit if form has data-hx-trigger-form or data-hx-inserted attribute
function hx_trigger() {
    let form = $('.modal-form');
    let trigger_name = form.attr("data-hx-trigger-form");
    let data_inserted = form.attr('data-hx-inserted');

    if (trigger_name === 'None' || trigger_name == undefined) {
        return;
    }

    if(trigger_name && data_inserted) {
        htmx.trigger("body", trigger_name, { });
    }
}


// hide modal
function modal_hide() {
    $('#modal').hide();
    hx_trigger();
}
