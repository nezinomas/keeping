import pdfplumber

from .pdfs import table_pdf, text_pdf


def test_table_pdf_creates_pdf_with_text_and_table(tmp_path):
    path = tmp_path / "test.pdf"
    header = ("Name", "Qty", "Sum\nwith discount")
    rows = [
        ("Apple", "2 vnt.", "€1,20"),
        ("Pear", "0,5 kg", "€0,80"),
        ("", "", ""),
    ]

    result = table_pdf(path, text_above="ACME SHOP", header=header, rows=rows)

    assert result == path
    assert path.exists()

    with pdfplumber.open(path) as pdf:
        assert len(pdf.pages) == 1
        page = pdf.pages[0]
        text = page.extract_text()
        assert "ACME SHOP" in text

        tables = page.extract_tables()
        assert len(tables) == 1
        table = tables[0]

        assert len(table) == 4
        assert table[0] == list(header)

        assert table[1] == ["Apple", "2 vnt.", "€1,20"]
        assert table[2] == ["Pear", "0,5 kg", "€0,80"]

        assert table[3] == ["", "", ""]


def test_text_pdf_round_trips_lines_through_pdfplumber(tmp_path):
    path = tmp_path / "test.pdf"
    lines = [
        "MAXIMA LT, UAB",
        "Milk 3,95 A",
        "2,49 X 0,224 kg",
        "Kvito suma 14,51",
    ]

    result = text_pdf(path, lines)

    assert result == path
    assert path.exists()

    with pdfplumber.open(path) as pdf:
        assert len(pdf.pages) == 1
        page = pdf.pages[0]
        assert page.extract_text().splitlines() == lines


def test_text_pdf_puts_more_pages_after_the_first(tmp_path):
    path = text_pdf(tmp_path / "test.pdf", ["Page one"], more_pages=(["Page two"],))

    with pdfplumber.open(path) as pdf:
        assert [page.extract_text() for page in pdf.pages] == ["Page one", "Page two"]
