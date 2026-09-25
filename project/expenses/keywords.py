def normalise_keyword(text: str) -> str:
    """The one spelling rule: `Jogurt` and `jogurt` are the same Keyword."""
    return text.strip().casefold()
