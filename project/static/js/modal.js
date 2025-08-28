// Constants for modal and container IDs
const CONTAINERS = ['mainModalContainer', 'imgModalContainer'];
const FORM_FIELDS = ['price', 'fee', 'quantity', 'title', 'remark', 'attachment'];
const MODALS = {
    mainModal: null,
    imgModal: null
};


// Modal class to encapsulate modal behavior
class Modal {
    constructor(id) {
        this.id = id;
        this.container = document.querySelector(`#${id}Container`);
        this.form = this.container?.querySelector('#modal-form');
    }

    show() {
        this.container && (this.container.style.display = 'block');
    }

    hide() {
        if (!this.container) {
            return;
        }

        this.container.style.display = 'none';

        if(this.form) {
            this.#hxTrigger();
            this.form.remove();
        }
    }

    resetForm() {
        if (!this.form) {
            return;
        }

        let formSetForms = this.form.querySelector("#id_form-TOTAL_FORMS")?.value;

        FORM_FIELDS.forEach((field) => {
            if (formSetForms) {
                for(let i = 0; i < formSetForms; i++ ) {
                    this.#resetField(`#id_form-${i}-${field}`);
                };
            } else  {
                this.#resetField(`#id_${field}`)
            };
        });
    }

    resetErrorMessages() {
        if (!this.form) {
            return;
        }

        // Remove error messages and invalid classes
        this.form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
        this.form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    }

    #hxTrigger() {
        const triggerName = this.form?.dataset.hxTriggerForm;
        const dataInserted = this.form?.dataset.hxInserted;

        if (triggerName && triggerName !== 'None' && dataInserted) {
            htmx.trigger('body', triggerName, {});
        }
    }

    #resetField(field) {
        const input = this.form.querySelector(field);
        input && (input.value = '');
    }
}


function initializeModals() {
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
            MODALS[modalId]?.hide();
        }
    });


    // close modal on ESC
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal-close').forEach((button) => {
                const modalId = button.dataset.dismiss;
                MODALS[modalId]?.hide();
            });
        }
    });


    // close modal on outside (e.g. containerModal) click
    document.addEventListener('click', (event) => {
        const targetId = event.target.id;
        if (CONTAINERS.includes(targetId)) {
            const modalId = targetId.replace('Container', '');
            MODALS[modalId]?.hide();
        }
    });


    // show modal on click button with hx-target="#mainModal"
    htmx.on('htmx:afterSwap', (e) => {
        const targetId = e.detail.target?.id;
        const modal = new Modal(targetId)
        MODALS[targetId] = modal;
        modal.show();

        if (targetId === 'imgModal') {
            const url = e.detail.requestConfig?.triggeringEvent?.originalTarget?.dataset?.url;
            if (url) {
                const modalBodyInput = document.querySelector(`#${targetId} .modal-body`);
                modalBodyInput && (modalBodyInput.innerHTML = `<img src="${url}" />`);
            }
        }
    });


    // reload modal form with error messages or reset fields and close modal form
    htmx.on('htmx:beforeSwap', (e) => {
        const targetId = e.detail.target?.id;
        const response = e.detail.xhr?.response;

        // Exit if the target is not mainModal or there's a response
        if (targetId !== "mainModal" || response) {
            return;
        }

        MODALS.mainModal.resetErrorMessages();
        MODALS.mainModal.resetForm();

        const submitterId = e.detail.requestConfig?.triggeringEvent?.submitter?.id;
        if (submitterId === '_close') {
            MODALS.mainModal.hide();
        }

        e.detail.shouldSwap = false;
    });
};

// Initialize modals when the DOM is ready
document.addEventListener('DOMContentLoaded', initializeModals);