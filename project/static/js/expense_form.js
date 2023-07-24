/* sum prices */
function sum_prices() {
    let total_field = document.getElementById("id_price");
    let total_value = parseFloat(total_field.value);
    let price_field = document.getElementById("id_total_sum");
    let price_value = String(price_field.value).replaceAll(',', '.');

    price_value = eval(price_value.replace(/[^\d\-\.\+\/\*]/g, ''));

    if (!price_value || price_value === Infinity) {
        price_value = 0;
    }

    let final_price = total_value + price_value;
    if (!final_price || final_price <= 0) {
        final_price = 0;
    }

    total_field.value = final_price.toFixed(2);
    price_field.value = '';
};


$("#add_price").click(function () {
    sum_prices();
});


/*
Enter allowed in texarea
Enter on id_total_sum input calls sum_prices()
Enter disabled on rest of form inputs
*/
document.getElementById("dialog-form").addEventListener('keypress', function (e) {
    if (e.key === "Enter" && e.target.id == "id_total_sum") {
        e.preventDefault();
        sum_prices();
    }
});

htmx.on("htmx:beforeSwap", (e) => {
    if (e.detail.target.id == "dialog" && !e.detail.xhr.response) {
        /* find submit button id */
        let subbmiter = e.detail.requestConfig.triggeringEvent.submitter.id;

        if(subbmiter == '_new') {
            // reset fields values after submit
            const fields = {"quantity": 1, "price": 0};
            for (const [key, value] of Object.entries(fields)) {
                const field = $(`#id_${key}`);
                if(field) {
                    field.val(value);
                }
            }
        }
    }
})
