class UnrecognisedReceiptError(Exception):
    """No Shop parser recognises the PDF's text."""


class UnreadableReceiptTextError(Exception):
    """A converter could not read the raw text it was given."""
