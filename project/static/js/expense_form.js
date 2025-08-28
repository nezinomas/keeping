/* sum prices */
function sumPrices() {
    let totalField = document.getElementById("id_price");
    let priceField = document.getElementById("id_total_sum");

    let totalValue = parseFloat(totalField.value) || 0;
    let priceValue = priceField.value.replace(/,/g, ".");

    // Safely evaluate the expression, removing non-mathematical characters
    try {
        priceValue = eval(priceValue.replace(/[^\d\-\.\+\/\*]/g, ""));
        if (!priceValue || priceValue === Infinity) {
            priceValue = 0;
        }
    } catch (e) {
        priceValue = 0;
    }

    let finalPrice = totalValue + priceValue;
    if (!finalPrice || finalPrice <= 0) {
        finalPrice = 0;
    }

    totalField.value = finalPrice.toFixed(2);
    priceField.value = "";
};


document.getElementById("add_price").addEventListener("click", sumPrices);


/*
Enter allowed in texarea
Enter on id_total_sum input calls sumPrices()
Enter disabled on rest of form inputs
*/
document.getElementById("modal-form").addEventListener("keypress", (e) => {
    if (e.key === "Enter" && e.target.id === "id_total_sum") {
        e.preventDefault();
        sumPrices();
    }
});


htmx.on("htmx:beforeSwap", (e) => {
    const targetId = e.detail.target?.id;
    if (targetId !== 'mainModal' || e.detail.xhr.response) {
        return;
    }
    /* find submit button id */
    const submitterId = e.detail.requestConfig?.triggeringEvent?.submitter?.id;

    if(submitterId === "_new") {
        // reset fields values after submit
        const fields = {
            "quantity": 1,
            "price": "0.0"
        };

        for (const [key, value] of Object.entries(fields)) {
            const field = document.getElementById(`id_${key}`);
            field && (field.value = value);
        }

        // reset exception checkbox
        const exceptionCheckbox = document.getElementById("id_exception");
        if (exceptionCheckbox) {
            exceptionCheckbox.checked = false;
        }
    };
});
