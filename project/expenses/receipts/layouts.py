from .layout import Columns, TableLayout, TextLayout

BARBORA = TableLayout(
    marker='UAB "Barbora"',
    columns=Columns(
        title="Prekės pavadinimas",
        amount="Surinktas kiekis",
        price="Suma su nuolaida",
    ),
    total_label="Bendra suma",
)

MAXIMA = TextLayout(
    marker="MAXIMA LT, UAB",
    lines_start="Kvitas bazėje:",
    lines_end="=====",
    vat_classes=("A",),
    amount_separator=" X ",
    item_discount_prefix="AČIŪ nuolaida prekei:",
    shop_money_label="Atsiskaityta MAXIMOS pinigais",
    total_label="Kvito suma",
)
