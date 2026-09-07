import io
import json
import os
from pathlib import Path
import boto3
from dotenv import load_dotenv
import pandas as pd
import pyarrow

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

BUCKET_NAME = os.getenv("R2_bucket_name", "bcb-pipeline-bronze")

# Mapeamento do dataset e sua respectiva coluna de valor final
DATASETS_CONFIG = {
    "selic": "taxa_selic_diaria",
    "dolar": "cotacao_dolar",
    "ipca": "variacao_ipca_mensal",
    "ibcbr": "indice_ibcbr",
}


def get_r2_client():
  return boto3.client(
      service_name="s3",
      endpoint_url=os.getenv("endpoint_r2_url"),
      aws_access_key_id=os.getenv("r2_access_key_cloudflare"),
      aws_secret_access_key=os.getenv("r2_secret_access_key"),
      region_name="auto",
  )


def _get_latest_bronze_json(
    client, dataset_name: str
) -> list[dict] | dict | None:
  """Busca e carrega o arquivo JSON mais recente da pasta bronze no R2."""
  prefix = f"bronze/{dataset_name}/"
  response = client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)

  if "Contents" not in response or not response["Contents"]:
    print(f"[Silver] Nenhum arquivo encontrado em {prefix}")
    return None

  # Ordena pela data de modificação para sempre pegar o arquivo mais recente
  arquivos = sorted(
      response["Contents"], key=lambda x: x["LastModified"], reverse=True
  )
  chave_recente = arquivos[0]["Key"]

  obj = client.get_object(Bucket=BUCKET_NAME, Key=chave_recente)
  conteudo = obj["Body"].read().decode("utf-8")
  print(f"[Silver] Lendo arquivo bruto: {chave_recente}")
  return json.loads(conteudo)


def _upload_parquet_to_silver(
    client, df: pd.DataFrame, dataset_name: str
) -> None:
  """Converte o DataFrame para Parquet em memória e faz upload para silver/ no R2."""
  buffer = io.BytesIO()
  df.to_parquet(buffer, index=False, engine="pyarrow")
  buffer.seek(0)

  key = f"silver/{dataset_name}/{dataset_name}.parquet"
  client.put_object(
      Bucket=BUCKET_NAME,
      Key=key,
      Body=buffer.getvalue(),
      ContentType="application/octet-stream",
  )
  print(f"[Silver] Salvo com sucesso: s3://{BUCKET_NAME}/{key}")


def transformar_dataset(client, dataset_name: str, target_column: str) -> None:
  """Aplica o pipeline de limpeza e tipagem do Pandas para um dataset específico."""
  raw_data = _get_latest_bronze_json(client, dataset_name)
  if not raw_data:
    return

  df = pd.DataFrame(raw_data)

  # 1. Tratamento de Tipagem
  df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
  df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

  # 2. Renomeação de Schema
  df = df.rename(columns={"valor": target_column})

  # 3. Qualidade de dados: remove nulos, duplicatas e ordena no tempo
  df = (
      df.dropna(subset=["data", target_column])
      .drop_duplicates(subset=["data"])
      .sort_values("data")
      .reset_index(drop=True)
  )

  # 4. Upload para a camada Silver no R2
  _upload_parquet_to_silver(client, df, dataset_name)


def transformar_tudo() -> None:
  """Executa a transformação de todos os indicadores configurados."""
  print(" Iniciando transformação -> Silver Cloudflare R2...\n")
  client = get_r2_client()

  for dataset, coluna_destino in DATASETS_CONFIG.items():
    transformar_dataset(client, dataset, coluna_destino)

  print("\n Todas as tabelas Silver foram transformadas e salvas no R2")


if __name__ == "__main__":
  transformar_tudo()




    

