import io
import os
from pathlib import Path
import boto3
from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import pyarrow

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BUCKET_NAME = os.getenv("r2_bucket_name", "bcb-pipeline-bronze")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "pipeline-etl-r2")
GCP_DATASET_SILVER = os.getenv("GCP_DATASET_SILVER", "silver")
CREDENTIALS_PATH = BASE_DIR / "credentials" / "pipeline-etl-r2-3716a8fbc5d3.json"

TABELAS = ["selic", "dolar", "ipca", "ibcbr"]


def get_r2_client():
  return boto3.client(
      service_name="s3",
      endpoint_url=os.getenv("endpoint_r2_url"),
      aws_access_key_id=os.getenv("r2_access_key_cloudflare"),
      aws_secret_access_key=os.getenv("r2_secret_access_key"),
      region_name="auto",
  )


def get_bigquery_client():
  credentials = service_account.Credentials.from_service_account_file(
      CREDENTIALS_PATH
  )
  return bigquery.Client(credentials=credentials, project=GCP_PROJECT_ID)


def carregar_tabela(r2_client, bq_client, dataset_nome: str):
  # 1. Lê o Parquet da camada Silver no R2 diretamente para memória
  chave_r2 = f"silver/{dataset_nome}/{dataset_nome}.parquet"
  obj = r2_client.get_object(Bucket=BUCKET_NAME, Key=chave_r2)
  df = pd.read_parquet(io.BytesIO(obj["Body"].read()))

  # 2. Configura a tabela de destino no BigQuery
  tabela_destino = f"{GCP_PROJECT_ID}.{GCP_DATASET_SILVER}.stg_{dataset_nome}"

  job_config = bigquery.LoadJobConfig(
      write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
  )

  # 3. Executa a carga
  job = bq_client.load_table_from_dataframe(
      df, tabela_destino, job_config=job_config
  )
  job.result()  

  print(
      f"[BigQuery] Tabela `{tabela_destino}` carregada com sucesso! ({len(df)}"
      " registos)"
  )


def carregar_tudo_para_bigquery():
  print("A iniciar carga Silver (R2) -> BigQuery...\n")
  r2_client = get_r2_client()
  bq_client = get_bigquery_client()

  for tabela in TABELAS:
    carregar_tabela(r2_client, bq_client, tabela)

  print("\n Todas as 4 tabelas foram criadas/atualizadas no BigQuery!")


if __name__ == "__main__":
  carregar_tudo_para_bigquery()