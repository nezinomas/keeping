const FORM_FIELDS = ['price', 'fee', 'quantity', 'title', 'remark', 'attachment'];


class Modal {
    constructor(id) {
        this.id = id;
    }

    // read on each call: imgModal's container arrives with the Duomenys tab
    get container() {
        return document.querySelector(`#${this.id}Container`);
    }

    get form() {
        return this.container?.querySelector('.modal-form');
    }

    show() {
        const container = this.container;
        if (!container) {
            return;
        }

        container.style.display = 'block';

        // a pressed menu act keeps focus, and :focus-within would hold its menu open
        if (document.activeElement?.closest('.dropdown__menu')) {
            document.activeElement.blur();
        }
    }

    hide() {
        const container = this.container;
        if (!container) {
            return;
        }

        container.style.display = 'none';

        const form = this.form;
        if (form) {
            this.#hxTrigger(form);
            form.remove();
        }
    }

    resetForm() {
        const form = this.form;
        if (!form) {
            return;
        }

        const formSetForms = form.querySelector('#id_form-TOTAL_FORMS')?.value;

        FORM_FIELDS.forEach((field) => {
            if (formSetForms) {
                for (let i = 0; i < formSetForms; i++) {
                    this.#resetField(form, `#id_form-${i}-${field}`);
                }
            } else {
                this.#resetField(form, `#id_${field}`);
            }
        });
    }

    resetErrorMessages() {
        const form = this.form;
        if (!form) {
            return;
        }

        form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    }

    #hxTrigger(form) {
        const triggerName = form.dataset.hxTriggerForm;
        const dataInserted = form.dataset.hxInserted;

        if (triggerName && dataInserted) {
            htmx.trigger('body', triggerName, {});
        }
    }

    #resetField(form, field) {
        const input = form.querySelector(field);
        if (input) {
            input.value = '';
        }
    }
}


const MODALS = {
    mainModal: new Modal('mainModal'),
    imgModal: new Modal('imgModal')
};


function hideModalIn(container) {
    Object.values(MODALS).find((modal) => modal.container === container)?.hide();
}


function showImage(e) {
    const modal = MODALS.imgModal;
    const url = e.detail.ctx?.sourceElement?.dataset?.url;
    if (e.detail.ctx?.target?.id !== modal.id || !url) {
        return;
    }

    const image = document.createElement('img');
    image.src = url;
    modal.container?.querySelector('.modal-body')?.replaceChildren(image);
}


function initializeModals() {
    document.addEventListener('submit', (event) => {
        if (event.target.matches('.modal-form')) {
            event.preventDefault();
        }
    });


    // a backdrop click lands on the container itself, outside its dialog
    document.addEventListener('click', (event) => {
        if (event.target.matches('.modal, .modal-close')) {
            hideModalIn(event.target.closest('.modal'));
        }
    });


    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            document.querySelectorAll('.modal[style*="display: block"]').forEach(
                (container) => hideModalIn(container)
            );
        }
    });


    htmx.on('htmx:after:swap', (e) => {
        // an empty response closed the modal in before:swap, but htmx 4 still
        // fires this event for it and the dialog would reopen empty
        if (!e.detail.ctx?.text) {
            return;
        }

        MODALS[e.detail.ctx?.target?.id]?.show();
    });


    htmx.on('htmx:after:swap', showImage);


    htmx.on('htmx:before:swap', (e) => {
        const targetId = e.detail.ctx?.target?.id;
        const responseText = e.detail.ctx?.text;

        if (targetId !== MODALS.mainModal.id || responseText) {
            return;
        }

        MODALS.mainModal.resetErrorMessages();
        MODALS.mainModal.resetForm();

        const submitterId = e.detail.ctx?.request?.submitter?.id;
        if (submitterId === '_close') {
            MODALS.mainModal.hide();
        }

        // no preventDefault(): htmx 4 fires the HX-Trigger header only once the
        // swap completes, so cancelling a 204's swap would swallow that trigger
    });
}

document.addEventListener('DOMContentLoaded', initializeModals);