from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'matheus',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
}

with DAG(
    dag_id='pipeline_macroeconomia_bcb',
    default_args=default_args,
    description='Pipeline ponta a ponta: API BCB -> R2 -> BigQuery -> dbt Gold',
    schedule_interval='0 19 * * 1-5',  # Segunda a sexta às 19:00
    catchup=False,
) as dag:

  t1_extract = BashOperator(
      task_id='extract_data_bronze',
      bash_command='python /opt/airflow/src/extract_data.py',
  )

  t2_transform = BashOperator(
      task_id='transformation_data_silver',
      bash_command='python /opt/airflow/src/transformation_data.py',
  )

  t3_load = BashOperator(
      task_id='load_data_bigquery',
      bash_command='python /opt/airflow/src/load_data.py',
  )

  t4_dbt_run = BashOperator(
      task_id='dbt_run_gold',
      bash_command='cd /opt/airflow/dbt_bcb && dbt run',
  )

  t5_dbt_test = BashOperator(
      task_id='dbt_test_quality',
      bash_command='cd /opt/airflow/dbt_bcb && dbt test --profiles-dir /home/airflow/.dbt',
  )

  # Ordem de execução
  t1_extract >> t2_transform >> t3_load >> t4_dbt_run >> t5_dbt_test