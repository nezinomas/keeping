function initializeLitepicker(input) {
    // Check if Litepicker is defined
    if (typeof Litepicker === 'undefined') {
        // Optionally, retry initialization after a short delay
        setTimeout(() => initializeLitepicker(input), 100);
        return;
    }

    // Skip if already initialized
    if (input.dataset.litepickerInitialized === 'true') {
        return;
    }

    const config = {
        element: input,
        format: 'YYYY-MM-DD',
    };

    // Apply translations if available
    if (typeof datePickerTrans !== 'undefined') {
        config.lang = datePickerTrans.lang;
        config.months = datePickerTrans.months;
        config.weekdays = datePickerTrans.weekdays;
        config.weekdaysShort = datePickerTrans.weekdaysShort;
        config.tooltipText = datePickerTrans.tooltipText;
    }

    try {
        new Litepicker(config);
        input.dataset.litepickerInitialized = 'true';
    } catch (error) {
        console.error('Failed to initialize Litepicker:', error);
    }
}

// Initialize Litepicker for existing elements
function initializeAllLitepickers() {
    document.querySelectorAll('.date-picker:not([data-litepicker-initialized])').forEach(initializeLitepicker);
}

// Wait for Litepicker to be available before initializing
function waitForLitepicker(callback) {
    if (typeof Litepicker !== 'undefined') {
        callback();
    } else {
        setTimeout(() => waitForLitepicker(callback), 100);
    }
}

// Run on DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    waitForLitepicker(initializeAllLitepickers);
});

// Reinitialize for HTMX-loaded content
document.body.addEventListener('htmx:afterSettle', function(event) {
    waitForLitepicker(() => {
        event.target.querySelectorAll('.date-picker:not([data-litepicker-initialized])').forEach(initializeLitepicker);
    });
});