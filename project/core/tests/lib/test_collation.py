from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.collation import lt_title

# the user's alphabet, a space and punctuation before it, digits and Q, W, X after it
ORDERED = " &-" + "aąbcčdeęėfghiįyjklmnoprsštuųūvzž" + "0123456789qwx"
CHARS = ORDERED + ORDERED.upper()


def _by_rank(title: str) -> tuple[str, str]:
    ranks = "".join(chr(0x100 + ORDERED.index(char)) for char in title.casefold())
    return ranks, title


@given(st.lists(st.text(alphabet=CHARS, max_size=6), max_size=8))
@example(["Čekiai", "Drabužiai", "Cukrus"])
@example(["Bilietai", "Ąžuolas", "Autobusas"])
@example(["Jūra", "Ypatingos", "Įrankiai", "Ilgas"])
@example(["Sveikata", "Telefonas", "Šildymas"])
@example(["Žaidimai", "Zuikis", "Zara"])
@example(["kava", "KAVA", "Kava"])
@example(["Hobis - 3D", "Hobis - dviratis", "Web", "Vanduo"])
@example(["Autobusas", "Auto kita"])
@example(["Wc", "Žaidimai", "3D", "Quiz", "Xenon"])
def test_titles_sort_by_the_lithuanian_alphabet(titles):
    assert sorted(titles, key=lt_title) == sorted(titles, key=_by_rank)
