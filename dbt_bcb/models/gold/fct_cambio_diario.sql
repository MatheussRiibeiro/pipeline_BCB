{{ config(
    materialized='table',
    partition_by={
      "field": "data_cotacao",
      "data_type": "date",
      "granularity": "year"
    },
    cluster_by=["ano", "mes"]
) }}

with cambio_base as (
    select
        date(data) as data_cotacao,
        cotacao_dolar,
        lag(cotacao_dolar) over (order by date(data)) as cotacao_anterior
    from {{ source('silver', 'stg_dolar') }}
),

calculo_metricas as (
    select
        data_cotacao,
        extract(year from data_cotacao) as ano,
        extract(month from data_cotacao) as mes,
        cotacao_dolar,
        cotacao_anterior,

        -- 1. Médias Móveis de Tendência (Curto e Médio Prazo)
        round(avg(cotacao_dolar) over(order by data_cotacao rows between 6 preceding and current row), 4) as media_movel_7d,
        round(avg(cotacao_dolar) over(order by data_cotacao rows between 29 preceding and current row), 4) as media_movel_30d,

        -- 2. Variação Diária (Nominal e Percentual)
        round(cotacao_dolar - cotacao_anterior, 4) as variacao_nominal_diaria,
        round(((cotacao_dolar - cotacao_anterior) / nullif(cotacao_anterior, 0)) * 100, 2) as variacao_percentual_diaria,

        -- 3. Dispersão e Volatilidade (Desvio Padrão Móvel de 30 dias úteis)
        round(stddev(cotacao_dolar) over(order by data_cotacao rows between 29 preceding and current row), 4) as volatilidade_movel_30d,

        -- 4. Extremos da Janela Recente (Mínima e Máxima dos últimos 30 dias úteis)
        min(cotacao_dolar) over(order by data_cotacao rows between 29 preceding and current row) as min_recente_30d,
        max(cotacao_dolar) over(order by data_cotacao rows between 29 preceding and current row) as max_recente_30d
    from cambio_base
)

select
    data_cotacao,
    ano,
    mes,
    cotacao_dolar,
    variacao_nominal_diaria,
    variacao_percentual_diaria,
    media_movel_7d,
    media_movel_30d,
    volatilidade_movel_30d,
    min_recente_30d,
    max_recente_30d,

    -- 5. Classificação Qualitativa de Risco de Mercado
    case 
        when variacao_percentual_diaria >= 2.0 then 'Choque de Alta (Desvalorização Severa)'
        when variacao_percentual_diaria <= -2.0 then 'Choque de Baixa (Apreciação Severa)'
        when abs(variacao_percentual_diaria) >= 1.0 then 'Oscilação Elevada'
        else 'Normalidade'
    end as classificacao_mercado,

    -- 6. Sua flag original (mantida para filtros rápidos booleanos)
    case 
        when abs(variacao_percentual_diaria) >= 2.0 then 1 
        else 0 
    end as flag_estresse_cambial

from calculo_metricas