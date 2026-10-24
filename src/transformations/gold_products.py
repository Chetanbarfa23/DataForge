from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


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
        print("\n" + "=" * 60)
        print("DATAFORGE: SILVER TO GOLD PIPELINE")
        print("=" * 60)

        # 1. Read cleaned Silver data
        print("\n[1/5] Reading Silver Parquet data...")

        df = spark.read.parquet(SILVER_PATH)

        total_products = df.count()

        print(f"Products loaded: {total_products}")

        if total_products == 0:
            raise ValueError("Silver layer contains no products.")

        # 2. Overall business metrics
        print("\n[2/5] Calculating overall product metrics...")

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
        print("\n[3/5] Calculating category analytics...")

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
        print("\n[4/5] Finding products with low stock...")

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

        low_stock_products.show(truncate=False)

        # 5. Save Gold datasets
        print("\n[5/5] Saving Gold Parquet datasets...")

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

        print(f"\nGold datasets saved to: {GOLD_PATH}")

        print("\n" + "=" * 60)
        print("GOLD PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)

    finally:
        spark.stop()


if __name__ == "__main__":
    build_gold_analytics()