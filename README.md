DataForge — Enterprise-Grade Data Engineering Platform

DataForge is an end-to-end data engineering project designed to ingest product data from a real-world API, validate data quality, transform raw data into analytics-ready datasets, and store processed data in Amazon S3.

The project demonstrates automated data pipelines, distributed data processing with Apache Spark, workflow orchestration with Apache Airflow, data quality checks, and CI validation with GitHub Actions.

Project Goals

* Build an automated data ingestion pipeline.
* Validate data quality before processing.
* Transform raw data into structured analytical datasets.
* Implement Bronze, Silver, and Gold data layers.
* Orchestrate pipeline tasks using Apache Airflow.
* Store processed datasets in Amazon S3.
* Validate code and pipeline configuration through CI.

Architecture

              DummyJSON Products API
                        |
                        v
              Apache Airflow DAG
                        |
                        v
                Bronze Layer
              Raw JSON Product Data
                        |
                        v
                Data Validation
                        |
                        v
                 Silver Layer
             Cleaned Product Data
                  (Parquet)
                        |
                        v
                  Gold Layer
             Analytics-Ready Data
                  (Parquet)
                        |
                        v
                  Amazon S3
             Silver and Gold Storage

GitHub Actions validates the project through automated tests and Airflow DAG checks.

Technology Stack

Technology	Purpose
Python	Ingestion, validation, and pipeline logic
Apache Airflow	Workflow orchestration
Apache Spark / PySpark	Distributed data transformation
Parquet	Columnar data storage
Amazon S3	Cloud storage for processed datasets
Git and GitHub	Version control
GitHub Actions	Continuous integration
pytest	Automated testing
Docker	Local development environment

Data Pipeline

The Airflow DAG is named dataforge_product_ingestion.

It contains six sequential tasks:

1. Ingest Products — Fetch product data from the API and store the raw JSON data.
2. Validate Product Data — Check product structure, identifiers, duplicate IDs, and prices.
3. Transform Silver — Clean and transform the raw product data using PySpark.
4. Upload Silver to S3 — Store the processed Silver dataset in Amazon S3.
5. Transform Gold — Generate analytics-ready datasets.
6. Upload Gold to S3 — Store the Gold datasets in Amazon S3.

The DAG is configured with retries, retry delays, failure logging, and a daily schedule.

Data Layers

Bronze — Raw Data

Stores the original product data retrieved from the API.

Silver — Cleaned Data

Contains cleaned product records with invalid records and duplicate product IDs removed.

The Silver data is stored in Parquet format.

Gold — Analytics Data

The Gold layer produces three datasets:

* overall_metrics — Overall product statistics, including product counts, price metrics, ratings, and stock.
* category_metrics — Product statistics grouped by category.
* low_stock_products — Products with stock below 10 units.

These datasets are stored in Parquet format for downstream analytical use.

Data Quality

The project includes validation checks for:

* Empty product datasets.
* Missing product IDs.
* Duplicate product IDs.
* Negative prices.
* Non-numeric prices.
* Boolean values incorrectly supplied as prices.
* Invalid product records.

Automated tests use pytest to verify ingestion and data validation behavior.

Continuous Integration

GitHub Actions runs automated checks when changes are pushed to the repository.

The CI workflow includes:

* Product API tests.
* Data quality tests.
* Airflow DAG import validation.
* Expected task and dependency validation.
* DAG retry and failure-callback configuration checks.

Running the Project Locally

Prerequisites

Install or configure the following:

* Python
* Docker Desktop
* Apache Airflow using the project’s Docker configuration
* Java, if required by your local PySpark setup
* AWS CLI, if using Amazon S3

1. Clone the repository

git clone https://github.com/Chetanbarfa23/DataForge.git
cd DataForge

2. Set up the Python environment

Create and activate a virtual environment if you do not already have one.

python -m venv .venv
source .venv/bin/activate

Install dependencies using the project’s configured dependency manager and lockfile.

3. Start the local environment

Use the Docker Compose configuration provided in the repository.

docker compose up -d

4. Access Airflow

Open the Airflow interface:

http://localhost:8080

Log in using the credentials configured by your local Airflow setup.

Locate the dataforge_product_ingestion DAG and trigger it when you are ready to execute the pipeline.

5. Run automated tests

From the project root:

python -m pytest

AWS Storage

The project uses Amazon S3 to store processed data.

Configure AWS credentials and the appropriate IAM permissions before running tasks that upload data to S3.

Do not commit AWS access keys, secret keys, passwords, or other credentials to the repository.

AWS usage may incur charges. Review your resources and billing before leaving cloud services running.

Repository Structure

DataForge/
├── dags/
│   └── product_ingestion_dag.py
├── src/
│   ├── connectors/
│   │   └── product_api.py
│   └── transformations/
│       ├── quality_checks.py
│       ├── silver_products.py
│       └── gold_products.py
├── tests/
│   ├── test_product_api.py
│   └── test_quality_checks.py
├── data/
│   └── local/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docker-compose.yaml
├── pyproject.toml
└── README.md

The exact repository contents may evolve as the project grows.

Roadmap

Planned enhancements include:

* Kafka-based streaming ingestion.
* Streaming data processing with Spark Structured Streaming.
* Elasticsearch integration for fast product search and filtering.
* Expanded data quality and integration testing.
* Improved pipeline monitoring and observability.
* Additional AWS integration where practical and cost-effective.

These enhancements will be implemented incrementally as the project develops.

Author

Chetan Barfa

B.Tech — Electronics and Telecommunication Engineering

GitHub: https://github.com/Chetanbarfa23