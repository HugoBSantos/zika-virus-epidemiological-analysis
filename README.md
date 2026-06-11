# Zika Vírus — Banco de Dados e Análise Estatística Epidemiológica (SINAN 2018-2026)

Projeto de Banco de Dados / Modelagem Estatística que transforma os microdados do
SINAN sobre notificações de Zika vírus (2018-2026, ~236 mil registros) em um
banco de dados relacional auditado no PostgreSQL e em um conjunto de análises
estatísticas e dashboard interativo.

## Arquitetura

O projeto segue uma arquitetura em camadas (medallion):

```
data/bronze/   → dados brutos (CSV unificado do SINAN + tabela de municípios do IBGE)
data/silver/   → dados limpos, normalizados e tipados (parquet), espelhando o schema PostgreSQL
data/gold/     → resultados das análises estatísticas, prontos para o dashboard
```

```
┌────────────┐     ┌──────────────┐     ┌───────────────┐     ┌────────────────┐
│  bronze     │ →   │  silver       │ →   │  PostgreSQL    │     │  gold           │
│  (CSV/IBGE) │ ETL │  (parquet)    │ ETL │  (silver.*)    │     │  (parquet)      │
└────────────┘     └──────────────┘     └───────────────┘     └────────────────┘
                            │                     │                      ↑
                            │                     │  funções, triggers,  │
                            │                     │  views (SQL)         │
                            │                     ▼                      │
                            └──────────────► notebooks/05_analise_estatistica.ipynb
                                                                          │
                                                                          ▼
                                                              dashboard/ (Streamlit)
```

## Estrutura do projeto

```
├── main.py                       # orquestra o pipeline ETL (extract → transform → load)
├── requirements.txt
├── src/
│   ├── 01_extract.py             # baixa a tabela de municípios do IBGE (DTB)
│   ├── 02_transform.py           # CSV bruto → tabelas normalizadas (data/silver/*.parquet)
│   └── 03_load.py                # carrega os parquet do silver no PostgreSQL
├── sql/
│   ├── ddl/silver.sql            # schema relacional (tabelas, PKs, FKs)
│   └── functions/
│       ├── functions             # funções: idade_anos, resumo_epidemiologico_uf_ano,
│       │                          # detectar_e_marcar_duplicatas, inserir_notificacao_validada
│       ├── triggers              # auditoria (JSONB antes/depois) + validações clínicas
│       └── views.sql             # views para o dashboard (KPIs, séries, pirâmide etária...)
├── data/
│   ├── bronze/                   # dados brutos
│   ├── silver/                   # dados normalizados (parquet)
│   └── gold/                     # saídas das análises estatísticas (parquet)
├── notebooks/
│   └── 05_analise_estatistica.ipynb  # sazonalidade, tendência, previsão (Prophet), K-Means
└── dashboard/
    ├── loaders.py                # carregamento e agregação dos dados (silver + gold)
    └── app.py                    # dashboard interativo (Streamlit)
```

## Banco de dados (PostgreSQL)

### Modelagem (`sql/ddl/silver.sql`)

Schema `silver` com as tabelas `ufs`, `municipios`, `paises`, `regionais_saude`,
`unidades_notificadoras`, `pacientes`, `notificacoes_casos`, `obitos` e
`casos_encerrados`, com chaves primárias/estrangeiras e índices únicos.

### Funções (`sql/functions/functions`)

- **`silver.idade_anos(idade_codificada)`** — decodifica o campo `NU_IDADE_N`
  (ex.: `4025` → 25 anos, `3006` → 6 meses) para idade em anos.
- **`silver.resumo_epidemiologico_uf_ano(tipo_uf)`** — total de casos confirmados
  por UF e ano, considerando UF de notificação, residência ou infecção.
- **`silver.detectar_e_marcar_duplicatas()`** — identifica e marca (`nduplic = true`)
  notificações duplicadas (mesmo paciente, sintomas e UF de infecção).
- **`silver.inserir_notificacao_validada(...)`** — insere uma notificação validando
  classificação final, integridade referencial e consistência de datas.

### Triggers (`sql/functions/triggers`)

- **Auditoria** (`audit.sistema_logs`): `trg_audit_notificacoes_casos` e
  `trg_audit_pacientes` registram INSERT/UPDATE/DELETE com snapshot JSONB
  antes/depois.
- **Validação clínica**: data de encerramento não pode ser anterior à
  notificação; data de óbito só pode existir se `evolucao_caso` indicar óbito;
  a evolução do caso não pode ser alterada para algo diferente de óbito enquanto
  houver registro vinculado em `silver.obitos`.

### Views (`sql/functions/views.sql`)

| View | Descrição |
| --- | --- |
| `vw_serie_temporal_semanal` | Casos confirmados por ano/semana epidemiológica (`DT_SIN_PRI`) |
| `vw_casos_uf_ano` | Casos confirmados por UF provável de infecção e ano |
| `vw_piramide_etaria` | Distribuição de casos confirmados por faixa etária e sexo |
| `vw_vigilancia_gestantes` | Casos confirmados em gestantes por trimestre gestacional |
| `vw_kpis` | Cards de KPI: total de casos, óbitos, gestantes, em investigação |

## Análise estatística (`notebooks/05_analise_estatistica.ipynb`)

Notebook executado sobre `data/silver/*.parquet`, exportando os resultados para
`data/gold/`:

1. **Sazonalidade** — decomposição STL (tendência/sazonalidade/resíduo) da série
   semanal de casos confirmados e perfil sazonal médio por semana epidemiológica.
2. **Tendência por UF** — regressão linear `casos ~ ano` por UF provável de
   infecção, ranqueando crescimento/queda ao longo de 2018-2026.
3. **Previsão de casos (Prophet)** — modelo com sazonalidade anual, avaliado em
   holdout de 12 semanas e projetado para as próximas 12 semanas.
4. **Agrupamento de municípios (K-Means)** — municípios com ≥10 casos confirmados
   agrupados por perfil epidemiológico (volume, taxa de confirmação, idade média,
   % gestantes, % óbitos, % autóctones), com seleção de *k* via inércia/silhueta.

## Dashboard (`dashboard/app.py`)

Dashboard Streamlit com filtros globais (período e UF) e seis abas:

- **Visão Geral** — KPIs e série temporal semanal de casos confirmados.
- **Distribuição Geográfica** — casos por UF, série anual e tendência de longo prazo.
- **Perfil Demográfico** — pirâmide etária e vigilância de gestantes.
- **Sazonalidade & Previsão** — decomposição STL, perfil sazonal e previsão (Prophet).
- **Agrupamento de Municípios** — perfis de cluster (K-Means) e mapa PCA.
- **Insights** — principais achados gerados a partir das análises acima.

## Como executar

### 1. Instalar dependências

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows
pip install -r requirements.txt
```

### 2. Configurar conexão com o PostgreSQL

Copie `.env.example` para `.env` e defina `POSTGRES_URL`.

### 3. Rodar o pipeline ETL

```bash
python main.py
```

Isso baixa a tabela de municípios do IBGE, transforma o CSV bruto em
`data/silver/*.parquet` e carrega tudo no PostgreSQL (DDL + funções + triggers + views).

### 4. Executar a análise estatística

```bash
jupyter notebook notebooks/05_analise_estatistica.ipynb
```

Gera/atualiza os arquivos em `data/gold/`.

### 5. Rodar o dashboard

```bash
streamlit run dashboard/app.py
```
