import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import boto3
from dotenv import load_dotenv
import requests


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_r2_client():
  return boto3.client(
      service_name="s3",
      endpoint_url=os.getenv("endpoint_r2_url"),
      aws_access_key_id=os.getenv("r2_access_key_cloudflare"),
      aws_secret_access_key=os.getenv("r2_secret_access_key"),
      region_name="auto",
  )


def _upload_to_bronze(
    data: list | dict, dataset_name: str, filename: str
) -> None:
  client = get_r2_client()
  bucket = os.getenv("R2_BUCKET_NAME", "bcb-pipeline-bronze")

  key = f"bronze/{dataset_name}/{filename}"
  data_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

  client.put_object(
      Bucket=bucket,
      Key=key,
      Body=data_bytes,
      ContentType="application/json",
  )
  print(f"[extract] Enviado para s3://{bucket}/{key}")


# --- CONFIGURAÇÃO DE CABEÇALHOS DA API ---
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ),
    "Accept": "application/json",
}


def _get_date_params(anos: int = 1) -> dict:

  data_final = datetime.now().strftime("%d/%m/%Y")
  data_inicial = (datetime.now() - timedelta(days=anos * 365)).strftime(
      "%d/%m/%Y"
  )
  return {"dataInicial": data_inicial, "dataFinal": data_final}



def extract_selic(anos: int = 1) -> None:
  url = os.getenv("BCB_API_SELIC")
  params = _get_date_params(anos)

  response = requests.get(url, params=params, headers=HEADERS, timeout=15)
  response.raise_for_status()

  data_hoje = datetime.now().strftime("%Y-%m-%d")
  filename = f"selic_{data_hoje}.json"

  _upload_to_bronze(
      data=response.json(), dataset_name="selic", filename=filename
  )


def extract_dolar(anos: int = 1) -> None:
  url = os.getenv("BCB_API_DOLAR")
  params = _get_date_params(anos)

  response = requests.get(url, params=params, headers=HEADERS, timeout=15)
  response.raise_for_status()

  data_hoje = datetime.now().strftime("%Y-%m-%d")
  filename = f"dolar_{data_hoje}.json"

  _upload_to_bronze(
      data=response.json(), dataset_name="dolar", filename=filename
  )


def extract_ipca(anos: int = 1) -> None:
  url = os.getenv("BCB_API_IPCA")
  params = _get_date_params(anos)

  response = requests.get(url, params=params, headers=HEADERS, timeout=15)
  response.raise_for_status()

  data_hoje = datetime.now().strftime("%Y-%m-%d")
  filename = f"ipca_{data_hoje}.json"

  _upload_to_bronze(
      data=response.json(), dataset_name="ipca", filename=filename
  )


def extract_ibcbr(anos: int = 1) -> None:
  url = os.getenv("BCB_API_IBCBR")
  params = _get_date_params(anos)

  response = requests.get(url, params=params, headers=HEADERS, timeout=15)
  response.raise_for_status()

  data_hoje = datetime.now().strftime("%Y-%m-%d")
  filename = f"ibcbr_{data_hoje}.json"

  _upload_to_bronze(
      data=response.json(), dataset_name="ibcbr", filename=filename
  )

if __name__ == "__main__":
  
  print("Iniciando extração e upload para o R2...\n")
  extract_selic(anos=3)
  extract_dolar(anos=3)
  extract_ipca(anos=5)
  extract_ibcbr(anos=5)
  print("\n Ingestão concluída!")

