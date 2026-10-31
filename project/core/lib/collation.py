ALPHABET = "aąbcčdeęėfghiįyjklmnoprsštuųūvzž"
RANKS = {letter: rank for rank, letter in enumerate(ALPHABET)}

SPACE, LETTER, OTHER = 0, 1, 2


def _char_key(char: str) -> tuple[int, int]:
    if char in RANKS:
        return LETTER, RANKS[char]

    if char.isalnum():
        return OTHER, ord(char)

    return SPACE, ord(char)


def lt_title(title: str) -> tuple:
    """A sort key in the Lithuanian alphabet, each letter its own place, case folded."""
    return tuple(_char_key(char) for char in title.casefold()), title
