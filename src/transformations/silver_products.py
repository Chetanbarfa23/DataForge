from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    LongType,
    StringType,
    DoubleType,
)


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BRONZE_PATH = str(
    PROJECT_ROOT / "data" / "local" / "bronze" / "products" / "*.json"
)

SILVER_PATH = str(
    PROJECT_ROOT / "data" / "local" / "silver" / "products"
)


# ============================================================
# 2. CREATE SPARK SESSION
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
# 3. BRONZE TO SILVER TRANSFORMATION
# ============================================================

def transform_products():

    spark = create_spark_session()

    try:
        print("\n" + "=" * 60)
        print("DATAFORGE: BRONZE TO SILVER PIPELINE")
        print("=" * 60)

        # ----------------------------------------------------
        # STEP 1: READ BRONZE JSON FILES
        # ----------------------------------------------------

        print("\n[1/7] Reading Bronze JSON files...")

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
        print(f"Total product records read: {records_read}")

        if records_read == 0:
            raise ValueError(
                "No products found in Bronze files. "
                "Check the source JSON files."
            )

        # ----------------------------------------------------
        # STEP 2: SELECT REQUIRED COLUMNS AND CAST TYPES
        # ----------------------------------------------------

        print("\n[2/7] Selecting columns and standardizing data types...")

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

        print("\n[3/7] Removing records with invalid product IDs...")

        before_id_filter = df.count()

        df = df.filter(
            F.col("id").isNotNull()
            & (F.col("id") > 0)
        )

        invalid_ids_removed = before_id_filter - df.count()

        print(f"Invalid IDs removed: {invalid_ids_removed}")

        # ----------------------------------------------------
        # STEP 4: VALIDATE PRICES
        # ----------------------------------------------------

        print("\n[4/7] Validating product prices...")

        before_price_filter = df.count()

        df = df.filter(
            F.col("price").isNotNull()
            & (~F.isnan(F.col("price")))
            & (F.col("price") >= 0)
        )

        invalid_prices_removed = before_price_filter - df.count()

        print(f"Invalid prices removed: {invalid_prices_removed}")

        # ----------------------------------------------------
        # STEP 5: CLEAN TEXT COLUMNS
        # ----------------------------------------------------

        print("\n[5/7] Cleaning text columns...")

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

        print("\n[6/7] Removing duplicate product IDs...")

        before_deduplication = df.count()

        df = df.dropDuplicates(["id"])

        duplicate_records_removed = (
            before_deduplication - df.count()
        )

        print(
            f"Duplicate records removed: "
            f"{duplicate_records_removed}"
        )

        # Add the processing timestamp.
        df = df.withColumn(
            "processed_at",
            F.current_timestamp(),
        )

        cleaned_records = df.count()

        print(f"\nTotal records read: {records_read}")
        print(f"Final Silver records: {cleaned_records}")

        # ----------------------------------------------------
        # STEP 7: WRITE SILVER PARQUET FILES
        # ----------------------------------------------------

        print("\n[7/7] Writing Silver data in Parquet format...")

        (
            df.write
            .mode("overwrite")
            .parquet(SILVER_PATH)
        )

        print(f"Silver output: {SILVER_PATH}")

        # ----------------------------------------------------
        # VERIFY OUTPUT
        # ----------------------------------------------------

        print("\nVerifying saved Silver data...")

        silver_df = spark.read.parquet(SILVER_PATH)

        saved_records = silver_df.count()

        print(f"Records saved: {saved_records}")

        print("\nSample Silver records:")

        silver_df.show(10, truncate=False)

        print("\nSilver schema:")

        silver_df.printSchema()

        if saved_records != cleaned_records:
            raise RuntimeError(
                "Validation failed: saved record count "
                "does not match cleaned record count."
            )

        print("\n" + "=" * 60)
        print("SILVER PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)

    finally:
        spark.stop()


# ============================================================
# 4. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    transform_products()