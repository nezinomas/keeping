$(function () {
    var search = function () {
        $('#loader').addClass('is-active')

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

        var container = $(this).attr('data-update-container');
        var container2 = $(this).attr('data-update-container2');

        container = (container ? `#${container}` : '#ajax-content');
        container2 = (container2 ? `#${container2}` : '#ajax-content2');

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

                var _html = data.html;
                var _html2 = data.html2;

                if(_html) {
                    $(container).html(_html);
                }

                if(_html2) {
                    $(container2).html(_html2);
                }

                $('#search_form_data').html(data.html_form);

                $('#loader').removeClass('is-active')
            },
            error: function (xhr, status, error) {
                alert(`${error}\n\n${xhr.responseJSON.error}`)

                $('#loader').removeClass('is-active')
            }
        });
    };

    $(document).on('click', '.search_click', search);
});
