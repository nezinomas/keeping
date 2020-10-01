$(function () {
    var search = function () {
        var btn = $(this);
        var url = btn.data('url');

        if (url == undefined) {
            return;
        }

        // This prevents the form from submitting
        event.preventDefault();

        // Capture form input
        csrfmiddlewaretoken = $("#search_form").find("input[name='csrfmiddlewaretoken']").val();
        form_data = $('#search_form').serializeArray();
        form_data = JSON.stringify(form_data);

        $.ajax({
            url: url,
            type: 'POST',
            dataType: 'json',
            type: "POST",
            data: {
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "form_data": form_data
            },
            success: function (data) {
                $('#ajax-content').html(data.html);
                $('#search_form_data').html(data.html_form);
            },
            error: function (xhr, status, error) {
                alert(`${error}\n\n${xhr.responseJSON.error}`)
            }
        });
    };

    $(document).on('click', '.search_click', search);
});
