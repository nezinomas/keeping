$(function () {
    var inviteLoadForm = function(url) {
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
            },
        });
    };

    var inviteButtonClick = function () {
        var btn = $(this);
        inviteLoadForm(btn.attr("data-url"));
    };

    $(document).on('click', '.js-invite', inviteButtonClick);

});
