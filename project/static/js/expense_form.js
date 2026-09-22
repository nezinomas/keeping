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


/**
 * Resets form fields after submission if triggered by the "_new" button.
 */
function resetFormFields(event) {
    const targetId = event.detail.ctx?.target?.id;
    const responseText = event.detail.ctx?.text;

    // Exit if the target is not mainModal or there's response content
    if (targetId !== "mainModal" || responseText) {
        return;
    }

    const submitterId = event.detail.ctx?.request?.submitter?.id;

    if (submitterId === "_new") {
        // Exit if the active form is not an expense form
        const isExpenseForm = document.getElementById("id_total_sum") || document.getElementById("id_expense_type");
        if (!isExpenseForm) {
            return;
        }

        // Define default field values
        const defaultValues = {
            quantity: "1",
            price: "0.0"
        };

        // Reset form fields
        for (const [key, value] of Object.entries(defaultValues)) {
            const field = document.getElementById(`id_${key}`);
            field && (field.value = value);
        }

        // Reset exception checkbox
        const exceptionCheckbox = document.getElementById("id_exception");
        exceptionCheckbox && (exceptionCheckbox.checked = false);
    }
}


document.getElementById("add_price").addEventListener("click", sumPrices);


/*
Enter allowed in texarea
Enter on id_total_sum input calls sumPrices()
Enter disabled on rest of form inputs
*/
document.querySelector(".modal-form").addEventListener("keypress", (e) => {
    if (e.key === "Enter" && e.target.id === "id_total_sum") {
        e.preventDefault();
        sumPrices();
    }
});


htmx.on("htmx:before:swap", resetFormFields);