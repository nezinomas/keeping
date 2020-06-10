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
                    var total_sum = document.getElementById("id_total_sum");
                    if (price != null & total_sum != null) {
                        total_sum.value = price.value
                        price.value = '0.00';
                    }
                }
            },
        });
    };

    var saveForm = function (event) {
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

                    // for (var key in data.extra) {
                    //     $(`#${key}`).html(data.extra[key])
                    // }

                    $(`#${ajax_update_container}`).html(data.html_list);
                    $("#modal-form .modal-content").html(data.html_form);

                    var price = document.getElementById("id_price");
                    if (price) {
                        price.value = '0.00';
                    }

                    var title = document.getElementById("id_title");
                    if (title) {
                        title.value = ''
                    }

                    // on update close modal
                    if (action == 'update' || action == 'delete') {
                        $("#modal-form").modal("hide");
                    }

                    // save and close
                    if (event.data.save_close == true) {
                        $('#modal-form').modal('hide')
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
        var btn = $(this);
        loadForm(btn.data('url'))
    };


    /* Binding */
    $('.dblclick').on('dblclick', 'tr', loadFormDblClc);
    $('.dblclick').on('dblclick', 'div', loadFormDblClc);

    $(document).on('click', '.js-create', loadFormClc);
    $(".dblclick").on('click', '.js-delete', loadFormClc);

    $('#modal-form').on('click', "#submit", {save_close: false}, saveForm)
    $('#modal-form').on('click', "#save_close", {save_close: true}, saveForm)
});
