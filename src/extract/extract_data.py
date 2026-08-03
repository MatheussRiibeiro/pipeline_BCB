import requests
from pathlib import Path
import json 

def extract_data(url:str) -> list:
    response = requests.get(url)
    data = response.json()
    return data
