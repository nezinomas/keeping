function initializeLitepicker(input) {
    const config = {
        element: input,
        format: 'YYYY-MM-DD',
    };

    if (typeof datePickerTrans !== 'undefined') {
        config.lang = datePickerTrans.lang;
        config.months = datePickerTrans.months;
        config.weekdays = datePickerTrans.weekdays;
        config.weekdaysShort = datePickerTrans.weekdaysShort;
        config.tooltipText = datePickerTrans.tooltipText;
    }

    new Litepicker(config);

    // Mark input as initialized to prevent duplicates
    input.dataset.litepickerInitialized = 'true';
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.date-picker:not([data-litepicker-initialized])').forEach(initializeLitepicker);
});

// Reinitialize for HTMX-loaded content
document.body.addEventListener('htmx:load', function(event) {
    event.target.querySelectorAll('.date-picker:not([data-litepicker-initialized])').forEach(initializeLitepicker);
});
