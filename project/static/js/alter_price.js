$(document).ready(function () {
    document.getElementById('id_price').type = 'text';
    document.getElementById('id_fee').type = 'text';
});

var price_input = document.getElementById("id_price");
price_input.addEventListener("keyup", function (event) {
    event.preventDefault();

    var price = String(price_input.value).replaceAll(',', '.')

    price_input.value = price;
});

var fee_input = document.getElementById("id_fee");
if(fee_input) {
    fee_input.addEventListener("keyup", function (event) {
        event.preventDefault();

        var fee = String(fee_input.value).replaceAll(',', '.')

        fee_input.value = fee;
    });
}
