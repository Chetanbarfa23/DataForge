"""Ingest product data from DummyJSON into the Bronze layer."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import boto3
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_URL = "https://dummyjson.com/products"
PAGE_SIZE = 100
REQUEST_TIMEOUT = 30

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

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# API ingestion
# ---------------------------------------------------------------------------

def fetch_products() -> list[dict]:
    """Fetch and validate all products using API pagination."""

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
                timeout=REQUEST_TIMEOUT,
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

            if not products and skip < total:
                raise ValueError(
                    "API returned an empty page before all products were fetched."
                )

            for product in products:
                if not isinstance(product, dict):
                    raise ValueError("A product record is not a JSON object.")

                if product.get("id") is None:
                    raise ValueError("A product is missing its ID.")

            all_products.extend(products)

            logger.info(
                "Fetched %d products; total collected: %d",
                len(products),
                len(all_products),
            )

            # Stop safely if the API returns an empty final page.
            if not products:
                break

            skip += len(products)

    return all_products


# ---------------------------------------------------------------------------
# Bronze storage
# ---------------------------------------------------------------------------

def save_raw_products(products: list[dict]) -> Path:
    """Persist a raw JSON snapshot locally and return its file path."""

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    ingestion_time = datetime.now(timezone.utc)
    filename = f"products_{ingestion_time.strftime('%Y%m%dT%H%M%SZ')}.json"
    output_path = BRONZE_DIR / filename

    raw_data = {
        "source": API_URL,
        "ingested_at": ingestion_time.isoformat(),
        "record_count": len(products),
        "products": products,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            raw_data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    logger.info("Saved local Bronze file: %s", output_path)

    return output_path


# ---------------------------------------------------------------------------
# AWS S3 storage
# ---------------------------------------------------------------------------

def upload_raw_products_to_s3(output_path: Path) -> str:
    """Upload a saved Bronze JSON snapshot to the configured S3 prefix.

    The named AWS CLI profile is used for local development. In CI or other
    AWS environments, callers can provide credentials through the standard
    boto3 credential chain by setting AWS_PROFILE to None.
    """

    output_path = Path(output_path)
    s3_key = f"{S3_PREFIX}{output_path.name}"

    session_kwargs = {"region_name": AWS_REGION}

    # Use the developer's named profile locally, when configured.
    if AWS_PROFILE:
        session_kwargs["profile_name"] = AWS_PROFILE

    session = boto3.Session(**session_kwargs)
    s3 = session.client("s3")

    s3.upload_file(
        str(output_path),
        S3_BUCKET,
        s3_key,
    )

    s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
    logger.info("Uploaded Bronze snapshot to %s", s3_uri)

    return s3_uri


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the product ingestion and Bronze upload workflow."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    logger.info("Starting product data ingestion")

    products = fetch_products()

    if not products:
        raise ValueError("No products were returned by the API.")

    # Keep local persistence and cloud upload as separate operations.
    output_path = save_raw_products(products)
    s3_uri = upload_raw_products_to_s3(output_path)

    logger.info("Ingestion completed successfully")
    logger.info("Total products: %d", len(products))
    logger.info("Local file: %s", output_path)
    logger.info("S3 location: %s", s3_uri)


if __name__ == "__main__":
    main()
    