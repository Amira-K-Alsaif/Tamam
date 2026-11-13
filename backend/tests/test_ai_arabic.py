import pytest

from app.ai.arabic import normalize_arabic


@pytest.mark.parametrize(
    ("written", "plain"),
    [
        ("إِجَازَة", "اجازه"),
        ("أإآٱ", "اااا"),
        ("عَلَى", "علي"),
        ("إجـــازة", "اجازه"),
        ("  إجازة   سنوية  ", "اجازه سنويه"),
        ("VPN", "vpn"),
    ],
)
def test_spelling_variants_become_the_same_text(written, plain):
    assert normalize_arabic(written) == plain


def test_keeps_arabic_indic_digits():
    assert normalize_arabic("٢١ يوماً") == "٢١ يوما"
