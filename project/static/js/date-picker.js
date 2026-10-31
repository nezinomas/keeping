function initializeLitepicker(input) {
    return new Litepicker({
        element: input,
        format: 'YYYY-MM-DD',
        lang: datePickerTrans.lang,
        tooltipText: datePickerTrans.tooltipText,
    });
}


// a swapped-out form's picker stays on <body> until destroyed
(window.datePickers ?? []).forEach((picker) => picker.destroy());
window.datePickers = [...document.querySelectorAll('.date-picker')].map(initializeLitepicker);
