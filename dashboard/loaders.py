from pathlib import Path

import polars as pl
import streamlit as st

SILVER = Path(__file__).resolve().parent.parent / "data" / "silver"
GOLD = Path(__file__).resolve().parent.parent / "data" / "gold"

FAIXAS_ETARIAS = ["0-4", "5-9", "10-14", "15-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]


def _faixa_etaria(idade: pl.Expr) -> pl.Expr:
    return (
        pl.when(idade < 5).then(pl.lit("0-4"))
        .when(idade < 10).then(pl.lit("5-9"))
        .when(idade < 15).then(pl.lit("10-14"))
        .when(idade < 20).then(pl.lit("15-19"))
        .when(idade < 30).then(pl.lit("20-29"))
        .when(idade < 40).then(pl.lit("30-39"))
        .when(idade < 50).then(pl.lit("40-49"))
        .when(idade < 60).then(pl.lit("50-59"))
        .when(idade < 70).then(pl.lit("60-69"))
        .when(idade < 80).then(pl.lit("70-79"))
        .otherwise(pl.lit("80+"))
    )


@st.cache_data
def load_base():
    notificacoes = pl.read_parquet(SILVER / "notificacoes_casos.parquet")
    pacientes = pl.read_parquet(SILVER / "pacientes.parquet")
    ufs = pl.read_parquet(SILVER / "ufs.parquet")

    pacientes = pacientes.with_columns(
        idade_codificada_str=pl.col("idade_codificada").cast(pl.Utf8)
    ).with_columns(
        tipo=pl.col("idade_codificada_str").str.slice(0, 1),
        quantidade=pl.col("idade_codificada_str").str.slice(1).cast(pl.Float64),
    ).with_columns(
        idade_anos=pl.when(pl.col("tipo") == "4").then(pl.col("quantidade"))
        .when(pl.col("tipo") == "3").then(pl.col("quantidade") / 12.0)
        .when(pl.col("tipo") == "2").then(pl.col("quantidade") / 365.0)
        .when(pl.col("tipo") == "1").then(pl.col("quantidade") / 8760.0)
        .otherwise(None)
        .round(2)
    ).drop("idade_codificada_str", "tipo", "quantidade")

    base = (
        notificacoes
        .join(pacientes, on="paciente_id", how="left")
        .join(ufs, left_on="uf_provavel_infeccao", right_on="uf_id", how="left")
        .with_columns(
            ano=pl.col("data_notificacao").dt.year(),
            ano_sintomas=pl.col("data_primeiros_sintomas").dt.year(),
        )
    )
    return base, ufs


@st.cache_data
def load_gold():
    sazonalidade = pl.read_parquet(GOLD / "sazonalidade_semanal.parquet")
    perfil_sazonal = pl.read_parquet(GOLD / "perfil_sazonal_semana_epi.parquet")
    previsao = pl.read_parquet(GOLD / "previsao_casos_semanal.parquet")
    tendencia_uf = pl.read_parquet(GOLD / "tendencia_casos_uf.parquet")
    clusters = pl.read_parquet(GOLD / "clusters_municipios.parquet")
    return sazonalidade, perfil_sazonal, previsao, tendencia_uf, clusters


def filtrar_confirmados(base: pl.DataFrame, anos: tuple[int, int], sigla_ufs: list[str]) -> pl.DataFrame:
    df = base.filter(
        (pl.col("classificacao_final") == "Confirmado")
        & pl.col("ano").is_between(anos[0], anos[1])
    )
    if sigla_ufs:
        df = df.filter(pl.col("sigla").is_in(sigla_ufs))
    return df


def kpis(base: pl.DataFrame, anos: tuple[int, int], sigla_ufs: list[str]) -> dict:
    df = filtrar_confirmados(base, anos, sigla_ufs)
    return {
        "total_casos": df.height,
        "total_obitos": df.filter(pl.col("evolucao_caso") == "Óbito pelo agravo").height,
        "total_gestantes": df.filter(
            pl.col("idade_gestacional").is_in(["1º trimestre", "2º trimestre", "3º trimestre"])
        ).height,
        "aguardando_investigacao": base.filter(
            (pl.col("classificacao_final") == "Em investigação")
            & pl.col("ano").is_between(anos[0], anos[1])
            & (pl.col("sigla").is_in(sigla_ufs) if sigla_ufs else pl.lit(True))
        ).height,
    }


def serie_temporal_semanal(base: pl.DataFrame, anos: tuple[int, int], sigla_ufs: list[str]) -> pl.DataFrame:
    df = base.filter(
        (pl.col("classificacao_final") == "Confirmado")
        & pl.col("ano_sintomas").is_between(anos[0], anos[1])
    )
    if sigla_ufs:
        df = df.filter(pl.col("sigla").is_in(sigla_ufs))
    return (
        df.group_by("ano_sintomas", "semana_primeiros_sintomas")
        .agg(pl.len().alias("total_casos"))
        .sort("ano_sintomas", "semana_primeiros_sintomas")
    )


def casos_uf_ano(base: pl.DataFrame, anos: tuple[int, int], sigla_ufs: list[str]) -> pl.DataFrame:
    df = base.filter(
        (pl.col("classificacao_final") == "Confirmado")
        & pl.col("uf_provavel_infeccao").is_not_null()
        & pl.col("ano").is_between(anos[0], anos[1])
    )
    if sigla_ufs:
        df = df.filter(pl.col("sigla").is_in(sigla_ufs))
    return (
        df.group_by("sigla", "ano")
        .agg(pl.len().alias("total_casos"))
        .sort("sigla", "ano")
    )


def piramide_etaria(base: pl.DataFrame, anos: tuple[int, int], sigla_ufs: list[str]) -> pl.DataFrame:
    df = filtrar_confirmados(base, anos, sigla_ufs).filter(pl.col("sexo").is_in(["Masculino", "Feminino"]))
    return (
        df.with_columns(faixa_etaria=_faixa_etaria(pl.col("idade_anos")))
        .group_by("faixa_etaria", "sexo")
        .agg(pl.len().alias("total_casos"))
    )


def vigilancia_gestantes(base: pl.DataFrame, anos: tuple[int, int], sigla_ufs: list[str]) -> pl.DataFrame:
    df = filtrar_confirmados(base, anos, sigla_ufs)
    return (
        df.filter(pl.col("idade_gestacional").is_in(["1º trimestre", "2º trimestre", "3º trimestre"]))
        .group_by("idade_gestacional")
        .agg(pl.len().alias("total_casos"))
        .sort("idade_gestacional")
    )


def compute_insights(base: pl.DataFrame, sazonalidade: pl.DataFrame, perfil_sazonal: pl.DataFrame,
                      previsao: pl.DataFrame, tendencia_uf: pl.DataFrame, clusters: pl.DataFrame) -> dict:
    confirmados = base.filter(pl.col("classificacao_final") == "Confirmado")
    total_casos = confirmados.height
    total_obitos = confirmados.filter(pl.col("evolucao_caso") == "Óbito pelo agravo").height
    total_gestantes = confirmados.filter(
        pl.col("idade_gestacional").is_in(["1º trimestre", "2º trimestre", "3º trimestre"])
    ).height

    tendencia_significativa = tendencia_uf.filter(pl.col("p_value") < 0.10)
    crescimento_uf = tendencia_significativa.filter(pl.col("tendencia_casos_ano") > 0).sort("tendencia_casos_ano", descending=True)
    declinio_uf = tendencia_significativa.filter(pl.col("tendencia_casos_ano") < 0).sort("tendencia_casos_ano")

    pico_sazonal = perfil_sazonal.sort("media_casos", descending=True).head(1)

    n_forecast = previsao.height - sazonalidade.height
    media_recente = sazonalidade.tail(12)["casos"].mean()
    media_prevista = previsao.tail(n_forecast)["yhat"].mean()
    variacao_previsao = (media_prevista / media_recente - 1) * 100 if media_recente else 0.0

    cluster_risco = clusters.group_by("cluster").agg(
        pl.col("pct_obito").mean().alias("pct_obito_medio"),
        pl.col("pct_gestantes").mean().alias("pct_gestantes_medio"),
        pl.col("total_confirmados").sum().alias("total_confirmados"),
        pl.len().alias("n_municipios"),
    ).sort("pct_obito_medio", descending=True)

    return {
        "total_casos": total_casos,
        "total_obitos": total_obitos,
        "letalidade": total_obitos / total_casos * 100 if total_casos else 0.0,
        "total_gestantes": total_gestantes,
        "pct_gestantes": total_gestantes / total_casos * 100 if total_casos else 0.0,
        "crescimento_uf": crescimento_uf,
        "declinio_uf": declinio_uf,
        "pico_sazonal": pico_sazonal,
        "variacao_previsao": variacao_previsao,
        "n_forecast": n_forecast,
        "cluster_risco": cluster_risco,
    }
