import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from loaders import (
    FAIXAS_ETARIAS,
    casos_uf_ano,
    compute_insights,
    kpis,
    load_base,
    load_gold,
    piramide_etaria,
    serie_temporal_semanal,
    vigilancia_gestantes,
)

st.set_page_config(page_title="Zika Vírus — SINAN 2018-2026", layout="wide")

base, ufs = load_base()
sazonalidade, perfil_sazonal, previsao, tendencia_uf, clusters = load_gold()

st.title("Vigilância Epidemiológica — Zika Vírus (SINAN 2018-2026)")

with st.sidebar:
    st.header("Filtros")
    ano_min, ano_max = int(base["ano"].min()), int(base["ano"].max())
    anos = st.slider("Período (ano de notificação)", ano_min, ano_max, (ano_min, ano_max))
    siglas_disponiveis = sorted(ufs["sigla"].to_list())
    sigla_ufs = st.multiselect("UF provável de infecção", siglas_disponiveis)
    st.caption("Os filtros se aplicam às abas Visão Geral, Distribuição Geográfica e Perfil Demográfico. "
               "Sazonalidade, previsão e clusters foram calculados sobre toda a série (2018-2026).")

tab_visao, tab_geo, tab_demo, tab_sazo, tab_cluster, tab_insights = st.tabs([
    "Visão Geral",
    "Distribuição Geográfica",
    "Perfil Demográfico",
    "Sazonalidade & Previsão",
    "Agrupamento de Municípios",
    "Insights",
])

with tab_visao:
    indicadores = kpis(base, anos, sigla_ufs)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Casos confirmados", f"{indicadores['total_casos']:,}")
    col2.metric("Óbitos pelo agravo", f"{indicadores['total_obitos']:,}")
    col3.metric("Gestantes confirmadas", f"{indicadores['total_gestantes']:,}")
    col4.metric("Aguardando investigação", f"{indicadores['aguardando_investigacao']:,}")

    serie = serie_temporal_semanal(base, anos, sigla_ufs).to_pandas()
    serie = serie.sort_values(["ano_sintomas", "semana_primeiros_sintomas"])
    serie["periodo"] = serie["ano_sintomas"] + (serie["semana_primeiros_sintomas"] - 1) / 52
    serie["rotulo"] = serie["ano_sintomas"].astype(str) + "-S" + serie["semana_primeiros_sintomas"].astype(str).str.zfill(2)

    fig = px.line(
        serie, x="periodo", y="total_casos", hover_data={"rotulo": True, "periodo": False},
        title="Casos confirmados por semana epidemiológica (data dos primeiros sintomas)",
    )
    fig.update_layout(xaxis_title="Ano", yaxis_title="Casos confirmados")
    st.plotly_chart(fig, width='stretch')

with tab_geo:
    casos_uf = casos_uf_ano(base, anos, sigla_ufs).to_pandas()

    total_por_uf = casos_uf.groupby("sigla", as_index=False)["total_casos"].sum().sort_values("total_casos", ascending=False)
    fig = px.bar(total_por_uf, x="sigla", y="total_casos", title="Total de casos confirmados por UF provável de infecção")
    fig.update_layout(xaxis_title="UF", yaxis_title="Casos confirmados")
    st.plotly_chart(fig, width='stretch')

    top_ufs_default = total_por_uf.head(5)["sigla"].tolist()
    ufs_linha = st.multiselect("UFs para a série anual", siglas_disponiveis, default=top_ufs_default)
    if ufs_linha:
        fig = px.line(
            casos_uf[casos_uf["sigla"].isin(ufs_linha)], x="ano", y="total_casos", color="sigla", markers=True,
            title="Série anual de casos confirmados por UF",
        )
        st.plotly_chart(fig, width='stretch')

    st.subheader("Tendência de longo prazo por UF (2018-2026)")
    st.caption("Inclinação da regressão linear casos ~ ano, calculada sobre toda a série histórica.")
    tendencia_pd = tendencia_uf.sort("tendencia_casos_ano", descending=True).to_pandas()
    fig = px.bar(
        tendencia_pd, x="uf", y="tendencia_casos_ano", color="tendencia_casos_ano",
        color_continuous_scale="RdYlGn_r",
        title="Variação média de casos confirmados por ano (inclinação da regressão)",
    )
    fig.update_layout(xaxis_title="UF", yaxis_title="Casos/ano")
    st.plotly_chart(fig, width='stretch')
    st.dataframe(tendencia_pd, width='stretch', hide_index=True)

with tab_demo:
    col1, col2 = st.columns(2)

    with col1:
        piramide = piramide_etaria(base, anos, sigla_ufs).to_pandas()
        piramide["total_casos_sinal"] = piramide.apply(
            lambda row: -row["total_casos"] if row["sexo"] == "Masculino" else row["total_casos"], axis=1
        )
        piramide["faixa_etaria"] = pd.Categorical(piramide["faixa_etaria"], categories=FAIXAS_ETARIAS, ordered=True)
        piramide = piramide.sort_values("faixa_etaria")

        fig = px.bar(
            piramide, x="total_casos_sinal", y="faixa_etaria", color="sexo", orientation="h",
            title="Pirâmide etária dos casos confirmados",
        )
        fig.update_layout(xaxis_title="Casos confirmados (Masculino à esquerda)", yaxis_title="Faixa etária")
        st.plotly_chart(fig, width='stretch')

    with col2:
        gestantes = vigilancia_gestantes(base, anos, sigla_ufs).to_pandas()
        fig = px.bar(
            gestantes, x="idade_gestacional", y="total_casos",
            title="Vigilância de gestantes — casos confirmados por trimestre gestacional",
        )
        fig.update_layout(xaxis_title="Idade gestacional", yaxis_title="Casos confirmados")
        st.plotly_chart(fig, width='stretch')

with tab_sazo:
    sazo_pd = sazonalidade.to_pandas()
    fig = go.Figure()
    for coluna, nome in [("casos", "Casos observados"), ("tendencia", "Tendência"), ("sazonalidade", "Sazonalidade")]:
        fig.add_trace(go.Scatter(x=sazo_pd["semana"], y=sazo_pd[coluna], name=nome))
    fig.update_layout(title="Decomposição STL da série semanal de casos confirmados (2018-2026)", xaxis_title="Semana")
    st.plotly_chart(fig, width='stretch')

    perfil_pd = perfil_sazonal.to_pandas()
    fig = px.bar(
        perfil_pd, x="semana_epi", y="media_casos",
        title="Perfil sazonal médio — casos confirmados por semana epidemiológica",
    )
    fig.update_layout(xaxis_title="Semana epidemiológica", yaxis_title="Média de casos confirmados")
    st.plotly_chart(fig, width='stretch')

    st.subheader("Previsão de casos (Prophet)")
    previsao_pd = previsao.to_pandas()
    n_forecast = previsao_pd.shape[0] - sazo_pd.shape[0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sazo_pd["semana"], y=sazo_pd["casos"], name="Casos observados", mode="lines"))
    fig.add_trace(go.Scatter(x=previsao_pd["ds"], y=previsao_pd["yhat"], name="Previsão (ajuste + futuro)", mode="lines"))
    fig.add_trace(go.Scatter(
        x=pd.concat([previsao_pd["ds"], previsao_pd["ds"][::-1]]),
        y=pd.concat([previsao_pd["yhat_upper"], previsao_pd["yhat_lower"][::-1]]),
        fill="toself", fillcolor="rgba(0,100,80,0.15)", line=dict(color="rgba(255,255,255,0)"),
        name="Intervalo de confiança", showlegend=True,
    ))
    fig.update_layout(title=f"Casos observados e previsão para as próximas {n_forecast} semanas", xaxis_title="Semana", yaxis_title="Casos")
    st.plotly_chart(fig, width='stretch')

with tab_cluster:
    clusters_pd = clusters.to_pandas()

    feature_cols = ["total_confirmados", "taxa_confirmacao", "idade_media", "pct_gestantes", "pct_obito", "pct_autoctone"]
    X = clusters_pd[feature_cols].fillna(0)
    X_scaled = StandardScaler().fit_transform(X)
    coords = PCA(n_components=2, random_state=42).fit_transform(X_scaled)
    clusters_pd["pca_1"], clusters_pd["pca_2"] = coords[:, 0], coords[:, 1]

    perfil_cluster = clusters_pd.groupby("cluster")[feature_cols].mean().round(3)
    perfil_cluster["n_municipios"] = clusters_pd.groupby("cluster").size()
    st.subheader("Perfil médio por cluster")
    st.dataframe(perfil_cluster, width='stretch')

    fig = px.scatter(
        clusters_pd, x="pca_1", y="pca_2", color=clusters_pd["cluster"].astype(str),
        hover_data=["nome", "sigla"] + feature_cols,
        title="Municípios agrupados por perfil epidemiológico (K-Means + PCA)",
    )
    st.plotly_chart(fig, width='stretch')

    cluster_sel = st.multiselect("Filtrar por cluster", sorted(clusters_pd["cluster"].unique()))
    tabela = clusters_pd if not cluster_sel else clusters_pd[clusters_pd["cluster"].isin(cluster_sel)]
    st.dataframe(
        tabela[["nome", "sigla", "cluster"] + feature_cols].sort_values("total_confirmados", ascending=False),
        width='stretch', hide_index=True,
    )

with tab_insights:
    insights = compute_insights(base, sazonalidade, perfil_sazonal, previsao, tendencia_uf, clusters)

    st.subheader("Principais achados da análise estatística")

    col1, col2, col3 = st.columns(3)
    col1.metric("Casos confirmados (2018-2026)", f"{insights['total_casos']:,}")
    col2.metric("Letalidade", f"{insights['letalidade']:.2f}%")
    col3.metric("Casos em gestantes", f"{insights['pct_gestantes']:.1f}%")

    crescimento_uf = insights["crescimento_uf"]
    declinio_uf = insights["declinio_uf"]
    pico = insights["pico_sazonal"]

    bullets = []

    if crescimento_uf.height:
        row = crescimento_uf.row(0, named=True)
        bullets.append(
            f"**{row['uf']}** apresenta a maior tendência de crescimento de casos confirmados "
            f"(+{row['tendencia_casos_ano']:.1f} casos/ano em média, R²={row['r2']:.2f}), "
            "indicando necessidade de reforço da vigilância nessa UF."
        )
    else:
        bullets.append(
            "Nenhuma UF apresenta tendência estatisticamente significativa de **crescimento** de "
            f"casos confirmados no período — pelo contrário, **{declinio_uf.height} UFs** mostram "
            "queda significativa, sugerindo um cenário geral de redução da transmissão desde 2018."
        )

    if declinio_uf.height:
        row = declinio_uf.row(0, named=True)
        bullets.append(
            f"**{row['uf']}** apresenta a maior tendência de queda no número de casos confirmados "
            f"({row['tendencia_casos_ano']:.1f} casos/ano em média, R²={row['r2']:.2f})."
        )

    if pico.height:
        row = pico.row(0, named=True)
        bullets.append(
            f"O pico sazonal médio ocorre na **semana epidemiológica {int(row['semana_epi'])}** "
            f"({row['media_casos']:.1f} casos em média), reforçando o padrão de sazonalidade "
            "associada ao período chuvoso/verão e à proliferação do mosquito vetor."
        )

    variacao = insights["variacao_previsao"]
    direcao_previsao = "aumento" if variacao > 0 else "redução"
    bullets.append(
        f"O modelo Prophet projeta **{direcao_previsao} de aproximadamente {abs(variacao):.1f}%** "
        f"nos casos semanais para as próximas {insights['n_forecast']} semanas, em relação à média "
        "observada nas últimas 12 semanas da série."
    )

    cluster_risco = insights["cluster_risco"]
    if cluster_risco.height and cluster_risco.row(0, named=True)["pct_obito_medio"] > 0:
        top = cluster_risco.row(0, named=True)
        ressalva = " (grupo pequeno, requer cautela na generalização)" if top["n_municipios"] < 5 else ""
        bullets.append(
            f"O **cluster {top['cluster']}** concentra os municípios com maior taxa média de óbito "
            f"pelo agravo ({top['pct_obito_medio']:.2%}) entre {top['n_municipios']} municípios{ressalva}, "
            "sugerindo prioridade para investigação clínica e ações de resposta rápida nesses locais."
        )

    bullets.append(
        f"Do total de casos confirmados, **{insights['total_gestantes']:,}** ocorreram em gestantes "
        f"({insights['pct_gestantes']:.1f}%), reforçando a importância da vigilância da síndrome "
        "congênita associada ao Zika."
    )

    for b in bullets:
        st.markdown(f"- {b}")

    st.caption(
        "Insights gerados automaticamente a partir das análises de sazonalidade, tendência por UF, "
        "previsão (Prophet) e agrupamento de municípios (K-Means) — ver notebooks/05_analise_estatistica.ipynb."
    )
