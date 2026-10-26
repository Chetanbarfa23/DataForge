import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def configure_logging():
    """Configure logging when the script runs directly."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def validate_products(products):
    """
    Validate product records before they enter
    the next stage of the DataForge pipeline.
    """

    if not isinstance(products, list):
        raise ValueError("Products must be provided as a list.")

    if not products:
        raise ValueError("Product list cannot be empty.")

    seen_ids = set()

    for index, product in enumerate(products):

        if not isinstance(product, dict):
            raise ValueError(
                f"Record {index} must be a dictionary."
            )

        product_id = product.get("id")

        if product_id is None:
            raise ValueError(
                f"Record {index} is missing its product ID."
            )

        if product_id in seen_ids:
            raise ValueError(
                f"Duplicate product ID found: {product_id}"
            )

        seen_ids.add(product_id)

        price = product.get("price")

        # bool is a subclass of int in Python, so reject it explicitly.
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError(
                f"Product {product_id} has an invalid price."
            )

        if price < 0:
            raise ValueError(
                f"Product {product_id} has a negative price."
            )

    result = {
        "status": "passed",
        "total_records": len(products),
        "unique_product_ids": len(seen_ids),
    }

    logger.info(
        "Data quality validation passed: total_records=%d, "
        "unique_product_ids=%d",
        result["total_records"],
        result["unique_product_ids"],
    )

    return result


def main():
    """Read the latest Bronze JSON file and validate its products."""

    project_root = Path(__file__).resolve().parents[2]

    bronze_dir = (
        project_root
        / "data"
        / "local"
        / "bronze"
        / "products"
    )

    files = sorted(bronze_dir.glob("products_*.json"))

    if not files:
        raise FileNotFoundError(
            f"No product JSON files found in {bronze_dir}"
        )

    latest_file = files[-1]

    logger.info("Reading Bronze file: %s", latest_file)

    with latest_file.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    if not isinstance(raw_data, dict):
        raise ValueError("Bronze JSON must contain a JSON object.")

    products = raw_data.get("products")

    result = validate_products(products)

    logger.info("Data Quality Report")
    logger.info("Status: %s", result["status"])
    logger.info("Total records: %d", result["total_records"])
    logger.info(
        "Unique product IDs: %d",
        result["unique_product_ids"],
    )

    return result


if __name__ == "__main__":
    configure_logging()
    main()
