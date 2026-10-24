import json
import pytest
from src.connectors.product_api import (
    fetch_products,
    save_raw_products,
)

def test_fetch_products_success(monkeypatch):
    """Test fetching products from a successful API response."""

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "products": [
                    {"id": 1, "title": "Headphones"},
                    {"id": 2, "title": "Keyboard"},
                ],
                "total": 2,
            }

    class FakeSession:
        def get(self, url, params, timeout):
            assert params["limit"] == 100
            return FakeResponse()

    class FakeSessionContext:
        def __enter__(self):
            return FakeSession()

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    monkeypatch.setattr(
        "src.connectors.product_api.requests.Session",
        FakeSessionContext,
    )

    products = fetch_products()

    assert len(products) == 2
    assert products[0]["id"] == 1
    assert products[1]["title"] == "Keyboard"


def test_fetch_products_rejects_missing_id(monkeypatch):
    """Test that records without IDs are rejected."""

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "products": [
                    {"title": "Product without an ID"}
                ],
                "total": 1,
            }

    class FakeSession:
        def get(self, url, params, timeout):
            return FakeResponse()

    class FakeSessionContext:
        def __enter__(self):
            return FakeSession()

        def __exit__(self, exc_type, exc_value, traceback):
            return False

    monkeypatch.setattr(
        "src.connectors.product_api.requests.Session",
        FakeSessionContext,
    )

    with pytest.raises(ValueError, match="missing its ID"):
        fetch_products()


def test_save_raw_products(tmp_path, monkeypatch):
    """Test that products are saved as valid JSON."""

    from src.connectors import product_api

    monkeypatch.setattr(
        product_api,
        "BRONZE_DIR",
        tmp_path / "bronze" / "products",
    )

    products = [
        {"id": 1, "title": "Headphones", "price": 2999}
    ]

    output_path = save_raw_products(products)

    assert output_path.exists()

    with output_path.open(encoding="utf-8") as file:
        saved_data = json.load(file)

    assert saved_data["record_count"] == 1
    assert saved_data["products"] == products
    assert saved_data["source"] == product_api.API_URL
    assert "ingested_at" in saved_data