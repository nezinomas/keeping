$(function () {

    var loadForm = function(url) {
        if (url == undefined || !url) {
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

                // load url from list table to form
                $("#js-form").attr('action', url);

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
            data: new FormData($('.js-form')[0]), // The form with the file inputs.
            processData: false,
            contentType: false,
            type: form.attr("method"),
            dataType: 'json',
            success: function (data) {
                if (data.form_is_valid) {

                    $(`#${ajax_update_container}`).html(data.html_list);
                    $("#modal-form .modal-content").html(data.html_form);

                    var price = document.getElementById("id_price");
                    if (price) {
                        price.value = '0.00';
                    }

                    var qty = document.getElementById("id_quantity");
                    if (qty) {
                        qty.value = 1;
                    }

                    var title = document.getElementById("id_title");
                    if (title) {
                        title.value = ''
                    }

                    var remark = document.getElementById("id_remark");
                    if (remark) {
                        remark.value = ''
                    }

                    var exception = document.getElementById("id_exception");
                    if (exception) {
                        exception.checked = false;
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
    $(document).on('dblclick', '.dblclick', loadFormDblClc);

    $(document).on('click', '.js-create', loadFormClc);
    $(document).on('click', '.js-delete', loadFormClc);

    $('#modal-form').on('click', "#submit", {save_close: false}, saveForm)
    $('#modal-form').on('click', "#save_close", {save_close: true}, saveForm)
});
