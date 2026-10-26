import logging
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


# =====================================================
# LOGGING CONFIGURATION
# =====================================================

logger = logging.getLogger(__name__)


def configure_logging():
    """Configure logging when the script runs directly."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# =====================================================
# PROJECT PATHS
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SILVER_PATH = str(
    PROJECT_ROOT / "data" / "local" / "silver" / "products"
)

GOLD_PATH = PROJECT_ROOT / "data" / "local" / "gold" / "products"


# =====================================================
# CREATE SPARK SESSION
# =====================================================

def create_spark_session():
    """Create a local Spark session for Gold analytics."""

    return (
        SparkSession.builder
        .appName("DataForge-Gold-Analytics")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


# =====================================================
# GOLD TRANSFORMATION
# =====================================================

def build_gold_analytics():

    spark = create_spark_session()

    try:
        logger.info("Starting DataForge Silver-to-Gold pipeline.")

        # 1. Read cleaned Silver data
        logger.info("Step 1/5: Reading Silver Parquet data.")

        df = spark.read.parquet(SILVER_PATH)

        total_products = df.count()

        logger.info("Products loaded: %d", total_products)

        if total_products == 0:
            raise ValueError("Silver layer contains no products.")

        # 2. Overall business metrics
        logger.info("Step 2/5: Calculating overall product metrics.")

        overall_metrics = df.agg(
            F.count("*").alias("total_products"),
            F.round(F.avg("price"), 2).alias("average_price"),
            F.round(F.min("price"), 2).alias("minimum_price"),
            F.round(F.max("price"), 2).alias("maximum_price"),
            F.round(F.avg("rating"), 2).alias("average_rating"),
            F.sum("stock").alias("total_stock"),
        )

        overall_metrics.show(truncate=False)

        # 3. Category-level analytics
        logger.info("Step 3/5: Calculating category analytics.")

        category_metrics = (
            df.groupBy("category")
            .agg(
                F.count("*").alias("product_count"),
                F.round(F.avg("price"), 2).alias("average_price"),
                F.round(F.avg("rating"), 2).alias("average_rating"),
                F.sum("stock").alias("total_stock"),
            )
            .orderBy(F.desc("product_count"))
        )

        category_metrics.show(truncate=False)

        # 4. Low-stock products
        logger.info("Step 4/5: Finding products with low stock.")

        low_stock_products = (
            df.filter(F.col("stock") < 10)
            .select(
                "id",
                "title",
                "category",
                "price",
                "stock",
            )
            .orderBy(F.asc("stock"))
        )

        low_stock_count = low_stock_products.count()

        logger.info("Products with stock below 10: %d", low_stock_count)

        low_stock_products.show(truncate=False)

        # 5. Save Gold datasets
        logger.info("Step 5/5: Saving Gold Parquet datasets.")

        GOLD_PATH.mkdir(parents=True, exist_ok=True)

        (
            overall_metrics
            .withColumn("generated_at", F.current_timestamp())
            .coalesce(1)
            .write
            .mode("overwrite")
            .parquet(str(GOLD_PATH / "overall_metrics"))
        )

        (
            category_metrics
            .withColumn("generated_at", F.current_timestamp())
            .write
            .mode("overwrite")
            .parquet(str(GOLD_PATH / "category_metrics"))
        )

        (
            low_stock_products
            .withColumn("generated_at", F.current_timestamp())
            .write
            .mode("overwrite")
            .parquet(str(GOLD_PATH / "low_stock_products"))
        )

        logger.info("Gold datasets saved to: %s", GOLD_PATH)

        logger.info(
            "Gold pipeline completed successfully. "
            "Total products=%d, low-stock products=%d",
            total_products,
            low_stock_count,
        )

    except Exception:
        logger.exception("Gold analytics transformation failed.")
        raise

    finally:
        spark.stop()
        logger.info("Spark session stopped.")


# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":
    configure_logging()
    build_gold_analytics()
