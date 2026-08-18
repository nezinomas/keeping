// a static file, not inline: an inline script re-inserted by an htmx swap loses
// its nonce, and production's CSP has no unsafe-inline to fall back on
function initCalendar() {
    const card = document.getElementById('heat-card');
    const tooltip = document.getElementById('heat-tooltip');
    if (!card || !tooltip) return;

    // anything labelled takes the tooltip; only the month grid takes the
    // keyboard walk, or the roving index would cross the same year twice
    const HOVER = '[data-label]';
    const CELL = '.mini i[data-label]';
    const cells = Array.from(card.querySelectorAll(CELL));
    let current = cells.length - 1;
    if (cells.length) cells[current].tabIndex = 0;

    function show(cell) {
        const label = cell.getAttribute('data-label');
        if (!label) return;

        const lines = label.split('\n');
        let html = `<div class="heat-tooltip__date">${lines[0] || ''}</div>`;
        if (lines[1]) html += `<div class="heat-tooltip__row">${lines[1]}</div>`;
        if (lines[2]) html += `<div class="heat-tooltip__row">${lines[2]}</div>`;

        tooltip.innerHTML = html;
        tooltip.style.borderColor = getComputedStyle(cell).backgroundColor;
        tooltip.style.display = 'block';

        positionTooltip(cell);
    }

    function hide() {
        tooltip.style.display = 'none';
    }

    // one cell holds the tab stop: a click that only set `current` left a second
    function rove(index) {
        cells[current].tabIndex = -1;
        current = Math.max(0, Math.min(index, cells.length - 1));
        cells[current].tabIndex = 0;
    }

    function moveTo(index) {
        rove(index);
        cells[current].focus();
    }

    card.addEventListener('mouseover', function (e) {
        const cell = e.target.closest(HOVER);
        cell ? show(cell) : hide();
    });

    card.addEventListener('mousemove', function (e) {
        const cell = e.target.closest(HOVER);
        if (cell && tooltip.style.display === 'block') {
            positionTooltip(cell);
        }
    });

    card.addEventListener('mouseleave', hide);

    card.addEventListener('click', function (e) {
        const cell = e.target.closest(CELL);
        if (cell) {
            moveTo(cells.indexOf(cell));
            return;
        }
        if (!e.target.closest(HOVER)) hide();
    });

    card.addEventListener('focusin', function (e) {
        const cell = e.target.closest(CELL);
        if (!cell) return;
        rove(cells.indexOf(cell));
        show(cell);
    });

    card.addEventListener('focusout', hide);

    const STEP = {ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7};

    card.addEventListener('keydown', function (e) {
        if (!e.target.closest(CELL)) return;

        let target;
        if (e.key in STEP) target = current + STEP[e.key];
        else if (e.key === 'Home') target = 0;
        else if (e.key === 'End') target = cells.length - 1;
        else return;

        e.preventDefault();
        moveTo(target);
    });

    function positionTooltip(cell) {
        const cellRect = cell.getBoundingClientRect();
        const cardRect = card.getBoundingClientRect();

        const left = cellRect.left - cardRect.left + (cellRect.width / 2);
        const top = cellRect.top - cardRect.top;

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }
}
