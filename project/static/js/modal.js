// prevent default form submission
$(document).on('submit', '.modal-form', function (e) {
    e.preventDefault();
});


// close modal on Close Buton
$(document).on('click', '.modal-close', function (e) {
    modal_hide($(this).data("dismiss"));
});


// close modal on ESC
$(document).keydown(function (event) {
    if (event.keyCode == 27) {
        $('.modal-close').each(function () {
            modal_hide($(this).data("dismiss"));
        })
    }
});


// close modal on outside (e.g. containerModal) click
window.onclick = function(event) {
    let containers = ['mainModalContainer', 'imgModalContainer'];

    if (containers.includes(event.target.id)) {
        // strip 'Container' prefix
        let target = event.target.id.replace('Container', '');
        modal_hide(target);
    }
}


// show modal on click button with hx-target="#mainModal"
htmx.on("htmx:afterSwap", (e) => {
    let target = e.detail.target.id;
    let modals = ['mainModal', 'imgModal'];

    if (modals.includes(target)) {
        $(`#${target}`).parent().show();

        // focus on [autofocus] field
        $(`#${target}`).find('[autofocus]').focus();

        // insert image url in imgModal
        if (target == 'imgModal') {
            let url = e.detail.requestConfig.triggeringEvent.originalTarget.dataset.url;
            let modalBodyInput = imgModal.querySelector('.modal-body .dspl');
            modalBodyInput.innerHTML = `<img src="${url}" />`;
        }
    }
})


// reload modal form with error messages or reset fields and close modal form
htmx.on("htmx:beforeSwap", (e) => {
    let target = e.detail.target.id;

    if (target == "mainModal" && !e.detail.xhr.response) {
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
            modal_hide(target);

            $('#modal-form .modal-form')[0].reset();
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
function modal_hide(target) {
    $(`#${target}`).parent().hide();
    hx_trigger();
}
