from datetime import datetime, timezone
from airflow.sdk import dag, task

@dag(
    dag_id="dataforge_product_ingestion",
    description="Automated Bronze, Silver, and Gold data pipeline",
    schedule="0 9 * * *",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    catchup=False,
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
        aws s3 cp data/local/silver/products/ s3://dataforge-bronze-chetan-2026/silver/products/ --recursive --exclude ".*" --profile datafrog --region ap-southeast-2
        """
    
    # Task 5: Generate Gold business analytics from Silver
    @task.bash
    def transform_gold():
        return """
        cd /opt/airflow/project &&
        python -m src.transformations.gold_products
        """
    
    # Task 6: uload gold analysis to s3
    @task.bash
    def upload_gold_to_s3():
        return """
        cd /opt/airflow/project &&
        aws s3 cp data/local/gold/products/ s3://dataforge-bronze-chetan-2026/gold/products/ --recursive --exclude ".*" --profile datafrog --region ap-southeast-2
        """
    
    # Define task dependencies
    ingestion = ingest_products()
    validation = validate_product_data()
    silver = transform_silver()
    silver_upload = upload_silver_to_s3()
    gold = transform_gold()
    gold_upload = upload_gold_to_s3()

    ingestion >> validation >> silver >> silver_upload >> gold >> gold_upload

# register the dag
product_ingestion_dag()


