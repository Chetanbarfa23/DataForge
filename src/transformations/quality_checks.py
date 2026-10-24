import json
from pathlib import Path


def validate_products(products):
    """
    Validate product records before they enter
    the next stage of the DataForge pipeline.
    """

    # Check 1: Input must be a list
    if not isinstance(products, list):
        raise ValueError("Products must be provided as a list.")

    # Check 2: Product list must not be empty
    if not products:
        raise ValueError("Product list cannot be empty.")

    # Store product IDs to detect duplicates
    seen_ids = set()

    # Validate each product
    for index, product in enumerate(products):

        # Check 3: Each record must be a dictionary
        if not isinstance(product, dict):
            raise ValueError(
                f"Record {index} must be a dictionary."
            )

        # Check 4: Product ID must exist
        product_id = product.get("id")

        if product_id is None:
            raise ValueError(
                f"Record {index} is missing its product ID."
            )

        # Check 5: Product IDs must be unique
        if product_id in seen_ids:
            raise ValueError(
                f"Duplicate product ID found: {product_id}"
            )

        seen_ids.add(product_id)

        # Check 6: Price must be numeric
        price = product.get("price")

        # bool is a subclass of int in Python, so reject it explicitly
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError(
                f"Product {product_id} has an invalid price."
            )

        # Check 7: Price must not be negative
        if price < 0:
            raise ValueError(
                f"Product {product_id} has a negative price."
            )

    # Return a summary when all checks pass
    return {
        "status": "passed",
        "total_records": len(products),
        "unique_product_ids": len(seen_ids),
    }


def main():
    """
    Read the latest Bronze JSON file and validate its products.
    """

    # Find the root directory of DataForge
    project_root = Path(__file__).resolve().parents[2]

    # Define the local Bronze directory
    bronze_dir = (
        project_root
        / "data"
        / "local"
        / "bronze"
        / "products"
    )

    # Find all timestamped product JSON files
    files = sorted(bronze_dir.glob("products_*.json"))

    # Stop if no files exist
    if not files:
        raise FileNotFoundError(
            f"No product JSON files found in {bronze_dir}"
        )

    # Select the latest file based on its timestamped filename
    latest_file = files[-1]

    print(f"Reading Bronze file: {latest_file}")

    # Load the JSON data
    with latest_file.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    # Extract product records
    products = raw_data.get("products")

    # Run data-quality checks
    result = validate_products(products)

    # Display the validation summary
    print("\nData Quality Report")
    print("-" * 40)
    print(f"Status: {result['status']}")
    print(f"Total records: {result['total_records']}")
    print(f"Unique product IDs: {result['unique_product_ids']}")
    print("-" * 40)

    return result


if __name__ == "__main__":
    main()