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
            }
        });
    };

    var saveForm = function() {
        var form = $('.js-form');
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
    $('table').on('dblclick', 'tr', loadFormDblClc);

    $(".js-create").click(loadFormClc);

    $('#modal-form').on('click', "#submit", saveForm)
});
