// Constants for modal and container IDs
const MODALS = ['mainModal', 'imgModal'];
const CONTAINERS = ['mainModalContainer', 'imgModalContainer'];
const FORM_FIELDS = ['price', 'fee', 'quantity', 'title', 'remark', 'attachment'];


// prevent default form submission
document.addEventListener('submit', (event) => {
    if (event.target.matches('.modal-form')) {
        event.preventDefault();
    }
});


// close modal on Close Buton
document.addEventListener('click', (event) => {
    if (event.target.matches('.modal-close')) {
        const modalId = event.target.dataset.dismiss;
        if (modalId) {
            modalHide(modalId);
        }
    }
});


// close modal on ESC
document.addEventListener('keydown', (event) => {
    if (event.keyCode === 27) {
        document.querySelectorAll('.modal-close').forEach((button) => {
            const modalId = button.dataset.dismiss;
            if (modalId) {
                modalHide(modalId);
            }
        });
    }
});


// close modal on outside (e.g. containerModal) click
document.addEventListener('click', (event) => {
    const targetId = event.target.id;
    if (CONTAINERS.includes(targetId)) {
        const modalId = targetId.replace('Container', '');
        modalHide(modalId);
    }
});


// show modal on click button with hx-target="#mainModal"
htmx.on('htmx:afterSwap', (event) => {
    const targetId = event.detail.target?.id;
    if (!MODALS.includes(targetId)) return;

    const modalContainer = document.querySelector(`#${targetId}Container`);
    if (modalContainer) {
        modalContainer.style.display = 'block';
    }

    if (targetId === 'imgModal') {
        const url = event.detail.requestConfig?.triggeringEvent?.originalTarget?.dataset?.url;
        if (url) {
            const modalBodyInput = document.querySelector(`#${targetId} .modal-body`);
            if (modalBodyInput) {
                modalBodyInput.innerHTML = `<img src="${url}" />`;
            }
        }
    }
});


// reload modal form with error messages or reset fields and close modal form
htmx.on('htmx:beforeSwap', (event) => {
    const targetId = event.detail.target?.id;
    if (targetId === 'mainModal' && !event.detail.xhr.response) {
        const submitterId = event.detail.requestConfig?.triggeringEvent?.submitter?.id;

        // Remove error messages
        document.querySelectorAll('.invalid-feedback').forEach((el) => el.remove());
        document.querySelectorAll('.is-invalid').forEach((el) => el.classList.remove('is-invalid'));

        if (submitterId === '_new') {
            // Reset fields
            FORM_FIELDS.forEach((field) => {
                const input = document.querySelector(`#id_${field}`);
                if (input) {
                    input.value = '';
                }
            });
        }

        if (submitterId === '_close') {
            modalHide(targetId);
            const form = document.querySelector('#modal-form .modal-form');
            if (form) {
                form.reset();
            }
        }

        event.detail.shouldSwap = false;
    }
});



// trigger htmx on form submit if form has data-hx-trigger-form or data-hx-inserted attribute
function hxTrigger() {
    const form = document.querySelector('.modal-form');
    const triggerName = form?.dataset.hxTriggerForm;
    const dataInserted = form?.dataset.hxInserted;

    if (triggerName && triggerName !== 'None' && dataInserted) {
        htmx.trigger('body', triggerName, {});
    }
}


// Hide modal
function modalHide(target) {
    const modalContainer = document.querySelector(`#${target}Container`);
    if (modalContainer) {
        modalContainer.style.display = 'none';
        hxTrigger();
    }
}
