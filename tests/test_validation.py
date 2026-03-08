from app.web.validation import is_valid_phone, normalize_phone


def test_normalize_phone() -> None:
    assert normalize_phone("+7 (999) 123-45-67") == "+79991234567"


def test_phone_validation() -> None:
    assert is_valid_phone("+79991234567")
    assert is_valid_phone("89991234567")
    assert not is_valid_phone("+7999")

