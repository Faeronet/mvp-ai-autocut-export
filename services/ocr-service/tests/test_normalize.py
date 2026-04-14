from app.postprocessing.engineering_normalize import normalize_text


def test_normalize_low_confidence():
    text, review = normalize_text("x", 0.2, "dimension_text")
    assert review is True


def test_normalize_pass():
    text, review = normalize_text("ГОСТ", 0.9, "notes")
    assert review is False


def test_engineering_symbol_fix():
    text, review = normalize_text("0 12", 0.85, "dimension_text")
    assert "Ø12" in text
    assert review is False
