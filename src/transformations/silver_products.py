import logging
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    LongType,
    StringType,
    DoubleType,
)


# ============================================================
# 1. LOGGING CONFIGURATION
# ============================================================

logger = logging.getLogger(__name__)


def configure_logging():
    """Configure logging when the script runs directly."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ============================================================
# 2. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_PATH = str(
    PROJECT_ROOT / "data" / "local" / "bronze" / "products" / "*.json"
)

SILVER_PATH = str(
    PROJECT_ROOT / "data" / "local" / "silver" / "products"
)


# ============================================================
# 3. CREATE SPARK SESSION
# ============================================================

def create_spark_session():
    """Create a local Spark session for DataForge."""

    return (
        SparkSession.builder
        .appName("DataForge-Silver-Products")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


# ============================================================
# 4. BRONZE TO SILVER TRANSFORMATION
# ============================================================

def transform_products():

    spark = create_spark_session()

    try:
        logger.info("Starting DataForge Bronze-to-Silver pipeline.")

        # ----------------------------------------------------
        # STEP 1: READ BRONZE JSON FILES
        # ----------------------------------------------------

        logger.info("Step 1/7: Reading Bronze JSON files.")

        raw_df = (
            spark.read
            .option("multiLine", True)
            .json(BRONZE_PATH)
        )

        # Verify that the expected products array exists.
        if "products" not in raw_df.columns:
            raise ValueError(
                "Expected a 'products' array in Bronze JSON files. "
                f"Found columns: {raw_df.columns}"
            )

        # Extract individual products from the products array.
        df = (
            raw_df
            .select(F.explode(F.col("products")).alias("product"))
            .select("product.*")
        )

        records_read = df.count()

        logger.info("Total product records read: %d", records_read)

        if records_read == 0:
            raise ValueError(
                "No products found in Bronze files. "
                "Check the source JSON files."
            )

        # ----------------------------------------------------
        # STEP 2: SELECT REQUIRED COLUMNS AND CAST TYPES
        # ----------------------------------------------------

        logger.info(
            "Step 2/7: Selecting required columns and standardizing data types."
        )

        expected_columns = {
            "id": LongType(),
            "title": StringType(),
            "description": StringType(),
            "category": StringType(),
            "price": DoubleType(),
            "discountPercentage": DoubleType(),
            "rating": DoubleType(),
            "stock": LongType(),
            "brand": StringType(),
        }

        for column, data_type in expected_columns.items():
            if column not in df.columns:
                df = df.withColumn(
                    column,
                    F.lit(None).cast(data_type),
                )
            else:
                df = df.withColumn(
                    column,
                    F.col(column).cast(data_type),
                )

        df = df.select(*expected_columns.keys())

        # ----------------------------------------------------
        # STEP 3: REMOVE INVALID PRODUCT IDS
        # ----------------------------------------------------

        logger.info("Step 3/7: Removing records with invalid product IDs.")

        before_id_filter = df.count()

        df = df.filter(
            F.col("id").isNotNull()
            & (F.col("id") > 0)
        )

        invalid_ids_removed = before_id_filter - df.count()

        logger.info("Invalid product IDs removed: %d", invalid_ids_removed)

        # ----------------------------------------------------
        # STEP 4: VALIDATE PRICES
        # ----------------------------------------------------

        logger.info("Step 4/7: Validating product prices.")

        before_price_filter = df.count()

        df = df.filter(
            F.col("price").isNotNull()
            & (~F.isnan(F.col("price")))
            & (F.col("price") >= 0)
        )

        invalid_prices_removed = before_price_filter - df.count()

        logger.info("Invalid product prices removed: %d", invalid_prices_removed)

        # ----------------------------------------------------
        # STEP 5: CLEAN TEXT COLUMNS
        # ----------------------------------------------------

        logger.info("Step 5/7: Cleaning text columns.")

        text_columns = [
            "title",
            "description",
            "category",
            "brand",
        ]

        for column in text_columns:
            cleaned_value = F.trim(F.col(column))

            df = df.withColumn(
                column,
                F.when(
                    cleaned_value == "",
                    F.lit(None).cast(StringType()),
                ).otherwise(cleaned_value),
            )

        # ----------------------------------------------------
        # STEP 6: REMOVE DUPLICATE PRODUCTS
        # ----------------------------------------------------

        logger.info("Step 6/7: Removing duplicate product IDs.")

        before_deduplication = df.count()

        df = df.dropDuplicates(["id"])

        duplicate_records_removed = (
            before_deduplication - df.count()
        )

        logger.info(
            "Duplicate product records removed: %d",
            duplicate_records_removed,
        )

        # Add the processing timestamp.
        df = df.withColumn(
            "processed_at",
            F.current_timestamp(),
        )

        cleaned_records = df.count()

        logger.info("Total Bronze records read: %d", records_read)
        logger.info("Final Silver records: %d", cleaned_records)

        # ----------------------------------------------------
        # STEP 7: WRITE SILVER PARQUET FILES
        # ----------------------------------------------------

        logger.info("Step 7/7: Writing Silver data in Parquet format.")

        (
            df.write
            .mode("overwrite")
            .parquet(SILVER_PATH)
        )

        logger.info("Silver output path: %s", SILVER_PATH)

        # ----------------------------------------------------
        # VERIFY OUTPUT
        # ----------------------------------------------------

        logger.info("Verifying saved Silver data.")

        silver_df = spark.read.parquet(SILVER_PATH)

        saved_records = silver_df.count()

        logger.info("Records saved: %d", saved_records)

        logger.info("Displaying sample Silver records.")
        silver_df.show(10, truncate=False)

        logger.info("Displaying Silver schema.")
        silver_df.printSchema()

        if saved_records != cleaned_records:
            raise RuntimeError(
                "Validation failed: saved record count "
                "does not match cleaned record count."
            )

        logger.info(
            "Silver pipeline completed successfully. "
            "Records read=%d, records written=%d",
            records_read,
            saved_records,
        )

    except Exception:
        logger.exception("Silver transformation failed.")
        raise

    finally:
        spark.stop()
        logger.info("Spark session stopped.")


# ============================================================
# 5. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    configure_logging()
    transform_products()