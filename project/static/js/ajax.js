$(function () {

    var loadForm = function(url) {
        if (url == undefined) {
            return;
        }

        $.ajax({
            url: url,
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $("#modal-form").modal("show").draggable({ handle: ".modal-header" });
            },
            success: function (data) {
                $("#modal-form .modal-content").html(data.html_form);

                var form = $('.js-form');
                var action = form.attr("data-action");
                if (action == 'update') {
                    var price = document.getElementById("id_price");
                    var total_sum = document.getElementById("total-sum");
                    if (price.value) {
                        total_sum.value = price.value
                        price.value = '0.00';
                    }
                }
            }
        });
    };

    var saveForm = function() {
        var form = $('.js-form');
        var action = form.attr("data-action");
        $.ajax({
            url: form.attr("action"),
            data: form.serialize(),
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.form_is_valid) {
                    $("#ajax-content").html(data.html_list);

                    var price = document.getElementById("id_price");
                    if (price.value) {
                        price.value = '0.00';
                    }
                    if (action == 'update') {
                        $("#modal-form").modal("hide");
                    }
                }
                else {
                    $("#modal-form .modal-content").html(data.html_form);
                }
            }
        });
        return false;
    };

    var loadFormClc = function() {
        var btn = $(this);
        loadForm(btn.attr("data-url"));
    };

    var loadFormDblClc = function () {
        loadForm($(this).data('url'))
    };


    /* Binding */
    $('#ajax-content').on('dblclick', 'tr', loadFormDblClc);

    $(".js-create").click(loadFormClc);

    $('#modal-form').on('click', "#submit", saveForm)
});
