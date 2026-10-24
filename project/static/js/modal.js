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

    get isOpen() {
        return this.container?.style.display === 'block';
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

        this.#fieldSelectors(form).forEach(
            (selector) => this.#resetField(form, selector)
        );
    }

    resetErrorMessages() {
        const form = this.form;
        if (!form) {
            return;
        }

        form.querySelectorAll('.invalid-feedback').forEach((el) => el.remove());
        form.querySelectorAll('.is-invalid').forEach(
            (el) => el.classList.remove('is-invalid')
        );
    }

    #hxTrigger(form) {
        const triggerName = form.dataset.hxTriggerForm;
        const dataInserted = form.dataset.hxInserted;

        if (triggerName && dataInserted) {
            htmx.trigger('body', triggerName, {});
        }
    }

    #fieldSelectors(form) {
        const totalForms = form.querySelector('#id_form-TOTAL_FORMS');
        if (!totalForms) {
            return FORM_FIELDS.map((field) => `#id_${field}`);
        }

        const rows = Array.from({ length: Number(totalForms.value) }, (_, i) => i);
        return FORM_FIELDS.flatMap(
            (field) => rows.map((i) => `#id_form-${i}-${field}`)
        );
    }

    #resetField(form, selector) {
        const input = form.querySelector(selector);
        if (input) {
            input.value = '';
        }
    }
}


const MODALS = {
    mainModal: new Modal('mainModal'),
    imgModal: new Modal('imgModal'),
};


function hideModalIn(container) {
    Object.values(MODALS).find((modal) => modal.container === container)?.hide();
}


function readSwap(e) {
    const ctx = e.detail.ctx;
    return {
        targetId: ctx?.target?.id,
        text: ctx?.text,
        url: ctx?.sourceElement?.dataset?.url,
        submitterId: ctx?.request?.submitter?.id,
    };
}


function showImage(e) {
    const modal = MODALS.imgModal;
    const { targetId, url } = readSwap(e);
    if (targetId !== modal.id || !url) {
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
            Object.values(MODALS).filter((modal) => modal.isOpen).forEach(
                (modal) => modal.hide()
            );
        }
    });


    htmx.on('htmx:after:swap', (e) => {
        const { targetId, text } = readSwap(e);
        // an empty response closed the modal in before:swap, but htmx 4 still
        // fires this event for it and the dialog would reopen empty
        if (!text) {
            return;
        }

        MODALS[targetId]?.show();
    });


    htmx.on('htmx:after:swap', showImage);


    htmx.on('htmx:before:swap', (e) => {
        const { targetId, text, submitterId } = readSwap(e);
        if (targetId !== MODALS.mainModal.id || text) {
            return;
        }

        MODALS.mainModal.resetErrorMessages();
        MODALS.mainModal.resetForm();

        if (submitterId === '_close') {
            MODALS.mainModal.hide();
        }

        // no preventDefault(): htmx 4 fires the HX-Trigger header only once the
        // swap completes, so cancelling a 204's swap would swallow that trigger
    });
}

document.addEventListener('DOMContentLoaded', initializeModals);
