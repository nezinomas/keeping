/* sum prices */
function sum_prices() {
    let input_total = document.getElementById("id_price");
    let input_price = document.getElementById("id_total_sum");
    let price = String(input_price.value).replaceAll(',', '.');
    let total = eval(input_total.value);

    price = eval(price.replace(/[^\d\-\.\+\/\*]/g, ''));

    if (!price || price === Infinity) {
        price = 0;
    }

    let res = total + price;
    if (!res || res <= 0) {
        res = 0;
    }

    input_total.value = res.toFixed(2);
    input_price.value = '';
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
    if (e.keyCode === 13 || e.which === 13) {
        if (e.target.id == "id_total_sum") {
            e.preventDefault();
            sum_prices();
        }
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
