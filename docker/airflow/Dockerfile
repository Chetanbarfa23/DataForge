FROM apache/airflow:3.1.0-python3.12

USER root

# Install Java and AWS CLI
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless \
        awscli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure Java for PySpark
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

USER airflow

# Install Python dependencies
RUN pip install --no-cache-dir \
    requests \
    boto3 \
    pyspark==4.2.0