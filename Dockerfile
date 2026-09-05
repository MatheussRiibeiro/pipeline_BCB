FROM apache/airflow:2.9.2-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends git && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow


RUN pip install --no-cache-dir \
    pandas \
    pyarrow \
    fastparquet \
    boto3 \
    python-dotenv \
    requests \
    google-cloud-bigquery \
    dbt-bigquery