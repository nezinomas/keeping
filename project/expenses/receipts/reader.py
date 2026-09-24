from dataclasses import dataclass

import pdfplumber

from . import converters
from .errors import UnrecognisedReceiptError
from .layouts import BARBORA
from .receipt import Receipt
from .shop_parser import ShopParser
from .table_parser import TableReceiptParser

PARSERS: tuple[ShopParser, ...] = (TableReceiptParser(BARBORA),)


@dataclass
class ReceiptReader:
    @classmethod
    def read(cls, file) -> Receipt:
        with pdfplumber.open(file) as document:
            text = "\n".join(
                converters.cell(page.extract_text()) for page in document.pages
            )
            for parser in PARSERS:
                if parser.recognises(text):
                    return parser.parse(document)
        raise UnrecognisedReceiptError()
