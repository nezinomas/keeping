$(document).on('click', '.paging', function () {
    var url = $(this).data('url');
    var page = $(this).data('page');
    var search = $(this).data('search');
    var container = $(this).data('container');

    $.ajax({
        type: 'GET',
        url: url,
        data: {
            page: page,
            search: search,
        },
        success: function (data) {
            var blocks = [container];
            reload_stats(data, blocks);
        },
        error: function () {
            alert('Paging has broken for unknown reason.')
        }
    });
});
