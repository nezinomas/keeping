$(function () {

    var loadForm = function(url, ajax_update_container = 'ajax-content') {
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
                form.attr('data-update-container', ajax_update_container)
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
        var ajax_update_container = form.attr('data-update-container')
        $.ajax({
            url: form.attr("action"),
            data: form.serialize(),
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.form_is_valid) {
                    $(`#${ajax_update_container}`).html(data.html_list);

                    var price = document.getElementById("id_price").value;
                    if (price) {
                        price = '0.00';
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
        loadForm(btn.attr("data-url"), btn.data("update-container"));
    };

    var loadFormDblClc = function () {
        loadForm($(this).data('url'), $(this).data('update-container'))
    };


    /* Binding */
    $('#ajax-content').on('dblclick', 'tr', loadFormDblClc);

    $(".js-create").click(loadFormClc);

    $('#modal-form').on('click', "#submit", saveForm)
});
