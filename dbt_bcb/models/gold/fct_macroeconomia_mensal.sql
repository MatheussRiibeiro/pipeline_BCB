{{ config(
    materialized='table',
    partition_by={
      "field": "data_referencia",
      "data_type": "date",
      "granularity": "year"
    }
) }}

with selic_mensal as (
    select
        date_trunc(date(data), month) as mes_ano,
        avg(taxa_selic_diaria) as selic_media_mensal,
        sum(taxa_selic_diaria) as selic_acumulada_mes
    from {{ source('silver', 'stg_selic') }}
    group by 1
),

dolar_mensal as (
    select
        date_trunc(date(data), month) as mes_ano,
        avg(cotacao_dolar) as dolar_medio_mensal,
        count(1) as dias_uteis_cambio
    from {{ source('silver', 'stg_dolar') }}
    group by 1
),

ipca_mensal as (
    select
        date_trunc(date(data), month) as mes_ano,
        variacao_ipca_mensal as ipca_mensal
    from {{ source('silver', 'stg_ipca') }}
),

ibcbr_mensal as (
    select
        date_trunc(date(data), month) as mes_ano,
        indice_ibcbr as ibcbr_mensal
    from {{ source('silver', 'stg_ibcbr') }}
),

consolidado as (
    select
        coalesce(s.mes_ano, d.mes_ano, i.mes_ano, b.mes_ano) as data_referencia,
        extract(year from coalesce(s.mes_ano, d.mes_ano, i.mes_ano, b.mes_ano)) as ano,
        extract(month from coalesce(s.mes_ano, d.mes_ano, i.mes_ano, b.mes_ano)) as mes,
        round(d.dolar_medio_mensal, 4) as dolar_medio,
        d.dias_uteis_cambio,
        round(s.selic_media_mensal, 4) as selic_media,
        round(s.selic_acumulada_mes, 4) as selic_acumulada_mes,
        round(i.ipca_mensal, 2) as ipca_mensal,
        round(b.ibcbr_mensal, 2) as ibcbr_indice
    from selic_mensal s
    full outer join dolar_mensal d on s.mes_ano = d.mes_ano
    full outer join ipca_mensal i on coalesce(s.mes_ano, d.mes_ano) = i.mes_ano
    full outer join ibcbr_mensal b on coalesce(s.mes_ano, d.mes_ano, i.mes_ano) = b.mes_ano
    where coalesce(s.mes_ano, d.mes_ano, i.mes_ano, b.mes_ano) is not null
)

select
    data_referencia,
    ano,
    mes,
    dolar_medio,
    dias_uteis_cambio,
    selic_media,
    selic_acumulada_mes,
    ipca_mensal,
    ibcbr_indice,

    -- 1. Inflação Acumulada em 12 Meses (Meta do Banco Central)
    round(sum(ipca_mensal) over(order by data_referencia rows between 11 preceding and current row), 2) as ipca_acumulado_12m,

    -- 2. Juro Real Ex-Post Mensal (Selic Acumulada no Mês - IPCA do Mês)
    round(selic_acumulada_mes - ipca_mensal, 2) as juro_real_mensal,

    -- 3. Juro Real Anualizado Estimado (Selic Média Anualizada - IPCA 12m)
    round(selic_media - sum(ipca_mensal) over(order by data_referencia rows between 11 preceding and current row), 2) as juro_real_anualizado_est,

    -- 4. Variação Econômica do PIB Mensal (MoM - Month over Month)
    round(
        ((ibcbr_indice - lag(ibcbr_indice, 1) over(order by data_referencia)) / nullif(lag(ibcbr_indice, 1) over(order by data_referencia), 0)) * 100, 
        2
    ) as ibcbr_crescimento_mom_pct,

    -- 5. Crescimento da Economia em Relação ao Ano Anterior (YoY - Year over Year)
    round(
        ((ibcbr_indice - lag(ibcbr_indice, 12) over(order by data_referencia)) / nullif(lag(ibcbr_indice, 12) over(order by data_referencia), 0)) * 100, 
        2
    ) as ibcbr_crescimento_yoy_pct,

    -- 6. Variação do Câmbio Médio Mensal (MoM)
    round(
        ((dolar_medio - lag(dolar_medio, 1) over(order by data_referencia)) / nullif(lag(dolar_medio, 1) over(order by data_referencia), 0)) * 100, 
        2
    ) as dolar_variacao_mensal_pct

from consolidado