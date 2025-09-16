function initializeLitepicker(input) {

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
    } catch (error) {
        console.error('Failed to initialize Litepicker:', error);
    }
};


document.querySelectorAll('.date-picker').forEach(initializeLitepicker);