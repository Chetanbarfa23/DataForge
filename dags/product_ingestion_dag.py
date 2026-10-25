from datetime import datetime, timezone, timedelta

from airflow.sdk import dag, task
from airflow.utils.log.logging_mixin import LoggingMixin


def task_failure_callback(context):
    """Log details when a DataForge task ultimately fails."""
    logger = LoggingMixin().log

    task_instance = context.get("ti")
    exception = context.get("exception")

    if task_instance:
        logger.error(
            "DataForge task failed: dag_id=%s, task_id=%s, run_id=%s",
            task_instance.dag_id,
            task_instance.task_id,
            task_instance.run_id,
        )

    if exception:
        logger.error("Failure reason: %s", exception)


@dag(
    dag_id="dataforge_product_ingestion",
    description="Automated Bronze, Silver, and Gold data pipeline",
    schedule="0 9 * * *",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    on_failure_callback=task_failure_callback,
    tags=["dataforge", "ingestion", "data-quality", "pyspark"],
)
def product_ingestion_dag():

    # Task 1: Ingest product data from the API into Bronze
    @task.bash
    def ingest_products():
        return """
        cd /opt/airflow/project &&
        python -m src.connectors.product_api
        """

    # Task 2: Validate the ingested Bronze data
    @task.bash
    def validate_product_data():
        return """
        cd /opt/airflow/project &&
        python -m src.transformations.quality_checks
        """

    # Task 3: Transform Bronze JSON into cleaned Silver Parquet
    @task.bash
    def transform_silver():
        return """
        cd /opt/airflow/project &&
        python -m src.transformations.silver_products
        """

    # Task 4: Upload Silver Parquet files to S3
    @task.bash
    def upload_silver_to_s3():
        return """
        cd /opt/airflow/project &&
        aws s3 sync data/local/silver/products/ s3://dataforge-bronze-chetan-2026/silver/products/ --delete --exclude ".*" --profile datafrog --region ap-southeast-2
        """

    # Task 5: Generate Gold business analytics from Silver
    @task.bash
    def transform_gold():
        return """
        cd /opt/airflow/project &&
        python -m src.transformations.gold_products
        """

    # Task 6: Upload Gold analytics to S3
    @task.bash
    def upload_gold_to_s3():
        return """
        cd /opt/airflow/project &&
        aws s3 sync data/local/gold/products/ s3://dataforge-bronze-chetan-2026/gold/products/ --delete --exclude ".*" --profile datafrog --region ap-southeast-2
        """

    # Define task dependencies
    ingestion = ingest_products()
    validation = validate_product_data()
    silver = transform_silver()
    silver_upload = upload_silver_to_s3()
    gold = transform_gold()
    gold_upload = upload_gold_to_s3()

    ingestion >> validation >> silver >> silver_upload >> gold >> gold_upload


# Register the DAG
product_ingestion_dag()