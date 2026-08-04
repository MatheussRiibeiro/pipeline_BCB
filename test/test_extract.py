import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
  sys.path.insert(0, str(BASE_DIR))


import src.extract_data as extract



def upload_local_mock(
    data: list | dict, dataset_name: str, filename: str
) -> None:

  local_dir = BASE_DIR / "data" / "bronze" / dataset_name
  local_dir.mkdir(parents=True, exist_ok=True)

  file_path = local_dir / filename
  data_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

  with open(file_path, "wb") as f:
    f.write(data_bytes)

  print(f"[teste local] Salvo com sucesso em: {file_path}")


def rodar_teste_local():
  print("Executando teste de extração local (Simulação)...\n")

  
  extract._upload_to_bronze = upload_local_mock

  
  print("Testando Selic...")
  extract.extract_selic(anos=1)

  print("Testando Dólar...")
  extract.extract_dolar()

  print("Testando IPCA...")
  extract.extract_ipca()

  print("Testando IBC-Br...")
  extract.extract_ibcbr()

  print("\nTodos os testes foram concluídos!")
  print("Confira os arquivos gerados dentro da pasta 'data/bronze/'.")


if __name__ == "__main__":
  rodar_teste_local()