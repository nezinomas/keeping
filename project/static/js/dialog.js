const modal = new bootstrap.Modal(document.getElementById("modal"))

htmx.on("htmx:afterSwap", (e) => {
    // Response targeting #dialog => show the modal
    if (e.detail.target.id == "dialog") {
        $("#modal").modal("show").draggable({ handle: ".modal-header" });
    }
})

function save() {
    htmx.on("htmx:beforeSwap", (e) => {
        // Empty response targeting #dialog => hide the modal
        if (e.detail.target.id == "dialog" && !e.detail.xhr.response) {
                $('#modal form')[0].reset();
            e.detail.shouldSwap = false;
        }
    })
}

function save_and_close() {
    htmx.on("htmx:beforeSwap", (e) => {
        // Empty response targeting #dialog => hide the modal
        if (e.detail.target.id == "dialog" && !e.detail.xhr.response) {
            modal.hide();

            $('#modal form')[0].reset();
            e.detail.shouldSwap = false;
        }
    })
}

$(document).keydown(function (event) {
    if (event.keyCode == 27) {
        $('#modal-form').modal("hide");
    }
});

// eh?
$(document).on('submit', '.js_form', function (e) {
    e.preventDefault();
});

// replace dot in year field
$(document).ready(function () {
    var fields = ['year', 'closed', 'valid_for'];
    var len = fields.length;
    for(i = 0; i < len; i++) {
        var field = fields[i];
        var year = $(`#id_${field}:text`).attr('value')
        if (year) {
            year = year.replace(".", "");
            year = year.replace(",", "");

            $(`#id_${field}`).attr('value', year);
            $(`#id_${field}:text`).val(year);
        }
    }
});
