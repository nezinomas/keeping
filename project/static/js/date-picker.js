function initializeLitepicker(input) {

    const config = {
        element: input,
        format: 'YYYY-MM-DD',
        lang: datePickerTrans.lang,
        tooltipText: datePickerTrans.tooltipText,
    };

    try {
        new Litepicker(config);
    } catch (error) {
        console.error('Failed to initialize Litepicker:', error);
    }
};


document.querySelectorAll('.date-picker').forEach(initializeLitepicker);