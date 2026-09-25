from typing import Protocol

import pdfplumber

from .receipt import Receipt


class ShopParser(Protocol):
    def recognises(self, text: str) -> bool: ...

    def parse(self, document: pdfplumber.PDF) -> Receipt: ...
