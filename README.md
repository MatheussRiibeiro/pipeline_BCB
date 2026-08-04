# Pipeline de Ingestão de Dados Financeiros — Banco Central do Brasil (BCB)

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![AWS S3 / R2](https://img.shields.io/badge/Cloud-Cloudflare_R2_(S3_Compatible)-orange.svg)
![Architecture](https://img.shields.io/badge/Architecture-Medallion_(Bronze)-bronze.svg)

Pipeline automatizado em Python para extração de indicadores econômicos da API do Banco Central do Brasil (SGS) e persistência na camada **Bronze** de um Data Lake (armazenado no Cloudflare R2 via protocolo S3).

---

## 📌 Indicadores Coletados

O pipeline realiza a ingestão diária e histórica dos seguintes dados:
* **Taxa Selic**: Taxa básica de juros da economia.
* **Cotação do Dólar**: Taxa de câmbio comercial (USD/BRL).
* **IPCA**: Índice Nacional de Preços ao Consumidor Amplo (inflação).
* **IBC-Br**: Índice de Atividade Econômica do Banco Central (prévia do PIB).

---

## Arquitetura e Estrutura do Projeto

```text
Pipeline_BCB/
├── config/                  # Configurações globais da aplicação
│   └── settings.py
├── data/                    # Dados salvos localmente (Apenas em ambiente de teste)
│   └── bronze/
│       ├── dolar/
│       ├── ibcbr/
│       ├── ipca/
│       └── selic/
├── src/                     # Código-fonte principal da aplicação
│   ├── __init__.py
│   ├── extract_data.py      # Script de ingestão da API do BCB -> Cloudflare R2
│   ├── load_data.py         # Carga e movimentação entre camadas
│   └── transformation_data.py # Regras de transformação de dados
├── test/                    # Suite de testes com execução local
│   └── test_extract.py      # Teste unitário/integrado com Mock de Upload
├── .env.example             # Template de variáveis de ambiente
├── .gitignore               # Proteção de credenciais e arquivos temporários
├── README.md                # Documentação do projeto
└── requirements.txt         # Dependências do projeto Python

[Python 3.11+]: Linguagem base do projeto.
[Requests]: Consumo da API RESTful do Banco Central com suporte a headers e parâmetros de data.
[Boto3]: SDK da AWS para integração com o armazenamento de objetos Cloudflare R2 via API S3.
[Python-Dotenv]: Gerenciamento seguro de variáveis de ambiente e segredos.