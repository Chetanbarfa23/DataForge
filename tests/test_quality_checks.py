import pytest

from src.transformations.quality_checks import validate_products


def test_valid_products():
    products = [
        {"id": 1, "title": "Headphones", "price": 2999},
        {"id": 2, "title": "Keyboard", "price": 1999},
    ]

    result = validate_products(products)

    assert result["status"] == "passed"
    assert result["total_records"] == 2
    assert result["unique_product_ids"] == 2


def test_missing_product_id():
    products = [
        {"title": "Headphones", "price": 2999}
    ]

    with pytest.raises(ValueError, match="missing its product ID"):
        validate_products(products)


def test_duplicate_product_ids():
    products = [
        {"id": 1, "title": "Headphones", "price": 2999},
        {"id": 1, "title": "Keyboard", "price": 1999},
    ]

    with pytest.raises(ValueError, match="Duplicate product ID"):
        validate_products(products)


def test_negative_price():
    products = [
        {"id": 1, "title": "Headphones", "price": -100}
    ]

    with pytest.raises(ValueError, match="negative price"):
        validate_products(products)


def test_empty_product_list():
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_products([])


def test_non_numeric_price():
    products = [
        {"id": 1, "title": "Headphones", "price": "abc"}
    ]

    with pytest.raises(ValueError, match="invalid price"):
        validate_products(products)


def test_boolean_price():
    products = [
        {"id": 1, "title": "Headphones", "price": True}
    ]

    with pytest.raises(ValueError, match="invalid price"):
        validate_products(products)
