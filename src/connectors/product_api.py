import json
from datetime import datetime, timezone
from pathlib import Path
import os
import boto3
import requests

# get request to get the data 
API_URL = "https://dummyjson.com/products"
PAGE_SIZE = 100

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_DIR = (
    PROJECT_ROOT
    / "data"
    / "local"
    / "bronze"
    / "products"
)

S3_BUCKET = "dataforge-bronze-chetan-2026"
S3_PREFIX = "bronze/products/"
AWS_REGION = "ap-southeast-2"
AWS_PROFILE = "datafrog"

def fetch_products():
    """
    Fetch all available products from the DummyJSON API.

    Uses pagination so that the pipeline can collect
    multiple pages of product data.
    """

    all_products = []
    skip = 0
    total = None

    with requests.Session() as session:

        while total is None or skip < total:

            params = {
                "limit": PAGE_SIZE,
                "skip": skip,
            }

            response = session.get(
                API_URL,
                params=params,
                timeout=30,
            )

            response.raise_for_status()

            payload = response.json()

            if not isinstance(payload, dict):
                raise ValueError("API response must be a JSON object.")

            products = payload.get("products")

            if not isinstance(products, list):
                raise ValueError(
                    "API response does not contain a valid products list."
                )

            if total is None:
                total = payload.get("total")

                if not isinstance(total, int) or total < 0:
                    raise ValueError("API returned an invalid total count.")

            if len(products) == 0 and skip < total:
                raise ValueError(
                    "API returned an empty page before all products were fetched."
                )

            for product in products:
                if not isinstance(product, dict):
                    raise ValueError("A product record is not a JSON object.")

                if product.get("id") is None:
                    raise ValueError("A product is missing its ID.")

            all_products.extend(products)

            print(
                f"Fetched {len(products)} products. "
                f"Total collected: {len(all_products)}"
            )

            skip += len(products)

    return all_products


def save_raw_products(products):
    """
    Save product data locally and upload the same JSON file to S3.
    """

    BRONZE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ingestion_time = datetime.now(timezone.utc)

    filename = (
        "products_"
        + ingestion_time.strftime("%Y%m%dT%H%M%SZ")
        + ".json"
    )

    output_path = BRONZE_DIR / filename

    raw_data = {
        "source": API_URL,
        "ingested_at": ingestion_time.isoformat(),
        "record_count": len(products),
        "products": products,
    }

    # 1. Save the data locally
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            raw_data,
            file,
            indent=2,
            ensure_ascii=False,
        )


    print(f"Saved local Bronze file: {output_path}")

    # 2. Connect to AWS using the named CLI profile
    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION,
    )

    s3 = session.client("s3")

    # 3. Build the S3 destination
    s3_key = f"{S3_PREFIX}{filename}"

    # 4. Upload the local JSON file to S3
    s3.upload_file(
        str(output_path),
        S3_BUCKET,
        s3_key,
    )

    print("\nIngestion completed successfully!")
    print(f"Total products: {len(products)}")
    print(f"Local file: {output_path}")
    print(f"S3 location: s3://{S3_BUCKET}/{s3_key}")

    return output_path

def main():
    print("Starting product data ingestion...")

    products = fetch_products()

    if not products:
        raise ValueError("No products were returned by the API.")

    save_raw_products(products)


if __name__ == "__main__":
    main()


