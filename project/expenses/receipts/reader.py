from dataclasses import dataclass

import pdfplumber
from pdfplumber.utils.exceptions import MalformedPDFException, PdfminerException

from . import converters
from .errors import UnreadableReceiptTextError, UnrecognisedReceiptError
from .layouts import BARBORA, MAXIMA
from .receipt import Receipt
from .shop_parser import ShopParser
from .table_parser import TableReceiptParser
from .text_parser import TextReceiptParser

PARSERS: tuple[ShopParser, ...] = (
    TableReceiptParser(BARBORA),
    TextReceiptParser(MAXIMA),
)


@dataclass
class ReceiptReader:
    @classmethod
    def read(cls, file) -> Receipt:
        try:
            return cls._read(file)
        except (PdfminerException, MalformedPDFException) as error:
            raise UnreadableReceiptTextError() from error

    @classmethod
    def _read(cls, file) -> Receipt:
        with pdfplumber.open(file) as document:
            text = "\n".join(
                converters.cell(page.extract_text()) for page in document.pages
            )
            for parser in PARSERS:
                if parser.recognises(text):
                    return cls._with_lines(parser.parse(document))
        raise UnrecognisedReceiptError()

    @classmethod
    def _with_lines(cls, receipt: Receipt) -> Receipt:
        if not receipt.lines:
            raise UnreadableReceiptTextError()
        return receipt
