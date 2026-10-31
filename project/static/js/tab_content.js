// draws a tab's chart on load and after each tab swap, wherever its data is on the page
function onTabContent(dataId, draw) {
    function drawIfShown() {
        if (document.getElementById(dataId)) {
            draw();
        }
    }

    document.addEventListener('DOMContentLoaded', drawIfShown);

    htmx.on('htmx:after:swap', function (event) {
        if (event.detail.ctx.target.id === 'tab_content') {
            drawIfShown();
        }
    });
}
