const FORM_FIELDS = ['price', 'fee', 'quantity', 'title', 'remark', 'attachment'];
const MODALS = {
    mainModal: null,
    imgModal: null
};


class Modal {
    constructor(id) {
        this.id = id;
        this.container = document.querySelector(`#${id}Container`);
        this.form = this.container?.querySelector('.modal-form');
    }

    show() {
        this.container && (this.container.style.display = 'block');

        // a pressed menu act keeps focus, and :focus-within would hold its menu open
        document.activeElement?.closest('.dropdown__menu') && document.activeElement.blur();
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

        this.form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
        this.form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    }

    #hxTrigger() {
        const triggerName = this.form?.dataset.hxTriggerForm;
        const dataInserted = this.form?.dataset.hxInserted;

        if (triggerName && dataInserted) {
            htmx.trigger('body', triggerName, {});
        }
    }

    #resetField(field) {
        const input = this.form.querySelector(field);
        input && (input.value = '');
    }
}


function initializeModals() {
    document.addEventListener('submit', (event) => {
        if (event.target.matches('.modal-form')) {
            event.preventDefault();
        }
    });


    document.addEventListener('click', (event) => {
        if (event.target.matches('.modal-close')) {
            const modalId = event.target.closest('.modal-dialog')?.id;
            if(modalId) {
                MODALS[modalId]?.hide();
            }
        }
    });


    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const visibleModals = document.querySelectorAll('.modal[style*="display: block"]');
            visibleModals.forEach((visibleModal) => {
                const modalId = visibleModal.querySelector('.modal-dialog')?.id;
                if(modalId) {
                    MODALS[modalId]?.hide();
                }
            });
        }
    });


    document.addEventListener('click', function(event) {
        const modalId = event.target.querySelector('div[id]')?.id;
        if (modalId) {
            MODALS[modalId]?.hide();
        }
    });


    htmx.on('htmx:after:swap', (e) => {
        // an empty response closed the modal in before:swap, but htmx 4 still
        // fires this event for it and the dialog would reopen empty
        if (!e.detail.ctx?.text) {
            return;
        }

        const targetId = e.detail.ctx?.target?.id;
        const modal = new Modal(targetId)
        MODALS[targetId] = modal;
        modal.show();

        if (targetId === 'imgModal') {
            const url = e.detail.ctx?.sourceElement?.dataset?.url;
            if (url) {
                const modalBodyInput = document.querySelector(`#${targetId} .modal-body`);
                modalBodyInput && (modalBodyInput.innerHTML = `<img src="${url}" />`);
            }
        }
    });


    htmx.on('htmx:before:swap', (e) => {
        const targetId = e.detail.ctx?.target?.id;
        const responseText = e.detail.ctx?.text;

        if (targetId !== "mainModal" || responseText) {
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
};

document.addEventListener('DOMContentLoaded', initializeModals);