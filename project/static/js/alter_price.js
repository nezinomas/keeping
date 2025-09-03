document.addEventListener("DOMContentLoaded", function () {
    const fields = ["id_price", "id_fee"];

    fields.forEach(field => {
        let element = document.getElementById(field);
        if (element) {
            element.type = "text";

            element.addEventListener("keyup", function (event) {
                event.preventDefault();
                let fieldValue = String(element.value).replaceAll(",", ".");
                element.value = fieldValue;
            });
        }
    });
});