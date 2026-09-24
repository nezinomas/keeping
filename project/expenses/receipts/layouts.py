from .layout import Columns, TableLayout

BARBORA = TableLayout(
    marker='UAB "Barbora"',
    columns=Columns(
        title="Prekės pavadinimas",
        amount="Surinktas kiekis",
        price="Suma su nuolaida",
    ),
    total_label="Bendra suma",
)
