$(document).ready(function () {
    const fields = ["id_price", "id_fee"];

    fields.forEach(field => {
        let element = document.getElementById(field);
        if (element) {
            element.type = "text";
        }
    });
});


let price_input = document.getElementById("id_price");
price_input.addEventListener("keyup", function (event) {
    event.preventDefault();

    let price = String(price_input.value).replaceAll(",", ".");

    price_input.value = price;
});


let fee_input = document.getElementById("id_fee");
if(fee_input) {
    fee_input.addEventListener("keyup", function (event) {
        event.preventDefault();

        let fee = String(fee_input.value).replaceAll(",", ".");

        fee_input.value = fee;
    });
}
