import os
from dotenv import load_dotenv

load_dotenv()

URL_SELIC = os.getenv("BCB_API_SELIC")
URL_IPCA = os.getenv("BCB_API_IPCA")
URL_DOLAR = os.getenv("BCB_API_DOLAR")