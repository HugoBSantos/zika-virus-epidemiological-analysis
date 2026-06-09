import logging
from pathlib import Path

import duckdb
import polars as pl

BRONZE = Path(__file__).resolve().parent.parent / "data" / "bronze"
SILVER = Path(__file__).resolve().parent.parent / "data" / "silver"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

_COLUMN_MAP = {
    "arquivo_origem": "arquivo_origem",
    "ano_arquivo": "ano_arquivo",
    "DT_NOTIFIC": "data_notificacao",
    "SEM_NOT": "semana_notificacao",
    "SG_UF_NOT": "uf_notificacao",
    "ID_MUNICIP": "municipio_notificacao",
    "ID_REGIONA": "codigo_regional",
    "DT_SIN_PRI": "data_primeiros_sintomas",
    "SEM_PRI": "semana_primeiros_sintomas",
    "NU_IDADE_N": "idade_codificada",
    "CS_SEXO": "sexo",
    "CS_GESTANT": "idade_gestacional",
    "CS_RACA": "raca_cor",
    "CS_ESCOL_N": "escolaridade",
    "SG_UF": "uf_residencia",
    "ID_MN_RESI": "municipio_residencia",
    "ID_RG_RESI": "regional_residencia",
    "ID_PAIS": "pais_residencia",
    "NDUPLIC_N": "notificacao_duplicada",
    "DT_INVEST": "data_investigacao",
    "CLASSI_FIN": "classificacao_final",
    "CRITERIO": "criterio_confirmacao",
    "TPAUTOCTO": "autoctonia",
    "COUFINF": "uf_provavel_infeccao",
    "COPAISINF": "pais_provavel_infeccao",
    "COMUNINF": "municipio_provavel_infeccao",
    "DOENCA_TRA": "doenca_trabalho",
    "EVOLUCAO": "evolucao_caso",
    "DT_OBITO": "data_obito",
    "DT_ENCERRA": "data_encerramento",
    "CS_FLXRET": "fluxo_retorno",
    "FLXRECEBI": "fluxo_recebido",
    "TPUNINOT": "tipo_unidade",
    "ID_UNIDADE": "codigo_unidade",
    "ANO_NASC": "ano_nascimento",
    "DT_DIGITA": "data_digitacao",
}

# IBGE XLS has numeric UF codes and full names but not the two-letter sigla
_UF_SIGLAS: dict[int, str] = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF",
}

# Categorical codes → readable labels for fields stored as VARCHAR in the schema.
# idade_codificada stays as raw integer; decoding belongs to a DB function.
_LABELS: dict[str, dict[str, str]] = {
    "sexo": {"M": "Masculino", "F": "Feminino", "I": "Ignorado"},
    "idade_gestacional": {
        "1": "1º trimestre", "2": "2º trimestre", "3": "3º trimestre",
        "4": "Idade gestacional ignorada", "5": "Não",
        "6": "Não se aplica", "9": "Ignorado",
    },
    "raca_cor": {
        "1": "Branca", "2": "Preta", "3": "Amarela",
        "4": "Parda", "5": "Indígena", "9": "Ignorado",
    },
    "escolaridade": {
        "0": "Analfabeto",
        "1": "1ª a 4ª série incompleta do EF",
        "2": "4ª série completa do EF",
        "3": "5ª a 8ª série incompleta do EF",
        "4": "Ensino Fundamental completo",
        "5": "Ensino Médio incompleto",
        "6": "Ensino Médio completo",
        "7": "Educação superior incompleta",
        "8": "Educação superior completa",
        "9": "Ignorado",
        "10": "Não se aplica",
    },
    "classificacao_final": {
        "0": "Descartado", "1": "Confirmado",
        "2": "Em investigação", "8": "Inconclusivo",
    },
    "criterio_confirmacao": {
        "0": "Em investigação", "1": "Laboratorial", "2": "Clínico-epidemiológico",
    },
    "autoctonia": {"1": "Sim", "2": "Não", "3": "Indeterminado"},
    "doenca_trabalho": {"1": "Sim", "2": "Não", "9": "Ignorado"},
    "evolucao_caso": {
        "0": "Em investigação", "1": "Cura", "2": "Óbito pelo agravo",
        "3": "Óbito por outra causa", "9": "Ignorado",
    },
}


def _case_map(field: str, labels: dict[str, str], default: str | None = None) -> str:
    """Return a SQL CASE expression that maps raw codes to readable labels."""
    branches = " ".join(f"WHEN {field} = '{k}' THEN '{v}'" for k, v in labels.items())
    else_clause = f"ELSE '{default}'" if default is not None else "ELSE NULL"
    return f"CASE {branches} {else_clause} END"


def _nullify(field: str) -> str:
    """SQL snippet that coerces empty strings and '/N' sentinels to NULL."""
    return f"NULLIF(NULLIF(TRIM({field}), ''), '/N')"


def _mun_fk(field: str) -> str:
    """FK lookup for a municipality field using the 6-digit SINAN prefix match."""
    return (
        f"(SELECT ml.municipio_id FROM mun_lookup ml "
        f"WHERE ml.sinan_code = LEFT({_nullify(field)}, 6))"
    )


def _load_csv(conn: duckdb.DuckDBPyConnection) -> None:
    col_select = ", ".join(f"{old} AS {new}" for old, new in _COLUMN_MAP.items())
    csv_path = str(BRONZE / "ZIKA_BR_2018_2026_UNIFICADO.csv").replace("\\", "/")
    conn.execute(f"""
        CREATE TABLE zika AS
        SELECT
            ROW_NUMBER() OVER () AS row_id,
            {col_select}
        FROM read_csv('{csv_path}', all_varchar = true)
    """)
    n = conn.execute("SELECT COUNT(*) FROM zika").fetchone()[0]
    log.info("CSV carregado → %d linhas", n)


def _build_ibge_tables(conn: duckdb.DuckDBPyConnection) -> None:
    ibge_raw = pl.read_excel(
        BRONZE / "RELATORIO_DTB_BRASIL_2025_MUNICIPIOS.xls",
        read_options={"header_row": 6},
    )
    # Locate column names by partial match to avoid breakage on minor header variation
    mun_code_col = next(c for c in ibge_raw.columns if "digo" in c and "Munic" in c)
    mun_nome_col = next(c for c in ibge_raw.columns if c.startswith("Nome") and "Munic" in c)
    ibge = ibge_raw.select([
        pl.col("UF").alias("uf_code"),
        pl.col("Nome_UF").alias("uf_nome"),
        pl.col(mun_code_col).alias("municipio_id"),
        pl.col(mun_nome_col).alias("municipio_nome"),
    ])
    conn.register("ibge", ibge)

    sigla_values = ", ".join(f"({code}, '{sigla}')" for code, sigla in _UF_SIGLAS.items())
    conn.execute(f"""
        CREATE TABLE uf_siglas AS
        SELECT * FROM (VALUES {sigla_values}) AS t(uf_id, sigla)
    """)

    conn.execute("""
        CREATE TABLE ufs AS
        SELECT DISTINCT
            CAST(uf_code AS SMALLINT) AS uf_id,
            s.sigla,
            uf_nome                  AS nome
        FROM ibge
        JOIN uf_siglas s ON CAST(uf_code AS SMALLINT) = s.uf_id
        ORDER BY uf_id
    """)
    log.info("ufs → %d linhas", conn.execute("SELECT COUNT(*) FROM ufs").fetchone()[0])

    conn.execute("""
        CREATE TABLE municipios AS
        SELECT DISTINCT
            CAST(municipio_id AS INT) AS municipio_id,
            municipio_nome            AS nome,
            CAST(uf_code AS SMALLINT) AS uf_id
        FROM ibge
        ORDER BY municipio_id
    """)
    log.info("municipios → %d linhas", conn.execute("SELECT COUNT(*) FROM municipios").fetchone()[0])

    # SINAN stores 6-digit codes (IBGE 7-digit without the check digit).
    # This lookup bridges the two representations for FK resolution.
    conn.execute("""
        CREATE TABLE mun_lookup AS
        SELECT LEFT(CAST(municipio_id AS VARCHAR), 6) AS sinan_code, municipio_id
        FROM municipios
    """)


def _build_paises(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE paises AS
        
        WITH id_paises_raw AS (
            SELECT pais_residencia        AS pais_id_raw FROM zika
            UNION
            SELECT pais_provavel_infeccao AS pais_id_raw FROM zika
        ),
        
        id_paises AS (
            SELECT
                TRY_CAST(pais_id_raw AS SMALLINT)              AS pais_id,
                CASE WHEN pais_id_raw = '1' THEN 'Brasil'
                     ELSE 'Desconhecido'
                END                                            AS nome
            FROM id_paises_raw
            WHERE pais_id_raw IS NOT NULL
              AND TRIM(pais_id_raw) NOT IN ('', '0', '/N')
        )
        
        SELECT DISTINCT pais_id, nome
        FROM id_paises
        WHERE pais_id IS NOT NULL
        ORDER BY pais_id
    """)
    log.info("paises → %d linhas", conn.execute("SELECT COUNT(*) FROM paises").fetchone()[0])


def _build_regionais(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE regionais_saude AS
        
        WITH regional_raw AS (
            SELECT codigo_regional    AS regional_id_raw, uf_notificacao AS uf_raw FROM zika
            UNION
            SELECT regional_residencia, uf_residencia                              FROM zika
        ),
        
        regional_casted AS (
            SELECT
                TRY_CAST(regional_id_raw AS SMALLINT) AS regional_id,
                TRY_CAST(uf_raw AS SMALLINT)          AS uf_id
            FROM regional_raw
            WHERE regional_id_raw IS NOT NULL
              AND TRIM(regional_id_raw) NOT IN ('', '/N')
              AND uf_raw IS NOT NULL
              AND TRIM(uf_raw) NOT IN ('', '/N')
        )
        
        SELECT DISTINCT regional_id, uf_id
        FROM regional_casted
        WHERE regional_id IS NOT NULL
          AND uf_id IN (SELECT uf_id FROM ufs)
        ORDER BY regional_id
    """)
    log.info("regionais_saude → %d linhas", conn.execute("SELECT COUNT(*) FROM regionais_saude").fetchone()[0])


def _build_unidades(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE unidades_notificadoras AS
        SELECT DISTINCT unidade_id, nome, tipo, municipio_id
        FROM (
            SELECT
                TRY_CAST(codigo_unidade AS INT)        AS unidade_id,
                NULL::VARCHAR                          AS nome,
                TRY_CAST(tipo_unidade AS SMALLINT)     AS tipo,
                (SELECT ml.municipio_id FROM mun_lookup ml
                 WHERE ml.sinan_code = LEFT(NULLIF(TRIM(municipio_notificacao), ''), 6)
                ) AS municipio_id
            FROM zika
            WHERE codigo_unidade IS NOT NULL
              AND TRIM(codigo_unidade) NOT IN ('', '/N', '0')
              AND municipio_notificacao IS NOT NULL
              AND TRIM(municipio_notificacao) NOT IN ('', '/N')
        )
        WHERE unidade_id IS NOT NULL
          AND municipio_id IS NOT NULL
        ORDER BY unidade_id
    """)
    log.info("unidades_notificadoras → %d linhas", conn.execute("SELECT COUNT(*) FROM unidades_notificadoras").fetchone()[0])


def _build_pacientes(conn: duckdb.DuckDBPyConnection) -> None:
    sexo_case  = _case_map("sexo", _LABELS["sexo"], "Ignorado")
    gest_case  = _case_map("idade_gestacional", _LABELS["idade_gestacional"], "Ignorado")
    raca_case  = _case_map("raca_cor", _LABELS["raca_cor"], "Ignorado")
    escol_case = _case_map("escolaridade", _LABELS["escolaridade"], "Ignorado")

    conn.execute(f"""
        CREATE TABLE pacientes AS
        SELECT
            row_id                                                AS paciente_id,
            TRY_CAST({_nullify('idade_codificada')} AS SMALLINT)  AS idade_codificada,
            {sexo_case}                                           AS sexo,
            {gest_case}                                           AS idade_gestacional,
            {raca_case}                                           AS raca_cor,
            {escol_case}                                          AS escolaridade,
            {_mun_fk('municipio_residencia')}                     AS municipio_id,
            CASE WHEN TRY_CAST({_nullify('regional_residencia')} AS SMALLINT)
                      IN (SELECT regional_id FROM regionais_saude)
                 THEN TRY_CAST({_nullify('regional_residencia')} AS SMALLINT)
                 ELSE NULL
            END                                                   AS regional_residencia,
            CASE WHEN TRY_CAST({_nullify('pais_residencia')} AS SMALLINT)
                      IN (SELECT pais_id FROM paises)
                 THEN TRY_CAST({_nullify('pais_residencia')} AS SMALLINT)
                 ELSE NULL
            END                                                   AS pais_id,
            NULL::VARCHAR                                         AS ocupacao
        FROM zika
    """)
    log.info("pacientes → %d linhas", conn.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0])


def _build_notificacoes(conn: duckdb.DuckDBPyConnection) -> None:
    classi_case  = _case_map("classificacao_final", _LABELS["classificacao_final"], "Em investigação")
    crit_case    = _case_map("criterio_confirmacao", _LABELS["criterio_confirmacao"])
    auto_case    = _case_map("autoctonia", _LABELS["autoctonia"], "Indeterminado")
    doenca_case  = _case_map("doenca_trabalho", _LABELS["doenca_trabalho"], "Ignorado")
    evolucao_case = _case_map("evolucao_caso", _LABELS["evolucao_caso"], "Ignorado")

    conn.execute(f"""
        CREATE TABLE notificacoes_casos AS
        SELECT
            row_id                                                   AS notificacao_id,
            row_id                                                   AS paciente_id,
            TRY_CAST(data_notificacao AS DATE)                       AS data_notificacao,
            TRY_CAST(RIGHT({_nullify('semana_notificacao')}, 2)
                AS SMALLINT)                                         AS semana_notificacao,
            CASE WHEN TRY_CAST({_nullify('codigo_unidade')} AS INT)
                      IN (SELECT unidade_id FROM unidades_notificadoras)
                 THEN TRY_CAST({_nullify('codigo_unidade')} AS INT)
                 ELSE NULL
            END                                                      AS unidade_id,
            CASE WHEN TRY_CAST({_nullify('codigo_regional')} AS SMALLINT)
                      IN (SELECT regional_id FROM regionais_saude)
                 THEN TRY_CAST({_nullify('codigo_regional')} AS SMALLINT)
                 ELSE NULL
            END                                                      AS regional_notificacao,
            TRY_CAST(data_primeiros_sintomas AS DATE)                AS data_primeiros_sintomas,
            TRY_CAST(RIGHT({_nullify('semana_primeiros_sintomas')}, 2)
                AS SMALLINT)                                         AS semana_primeiros_sintomas,
            TRY_CAST({_nullify('data_investigacao')} AS DATE)        AS data_investigacao,
            {classi_case}                                            AS classificacao_final,
            {crit_case}                                              AS criterio_confirmacao,
            {auto_case}                                              AS autoctonia,
            CASE WHEN TRY_CAST({_nullify('uf_provavel_infeccao')} AS SMALLINT)
                      IN (SELECT uf_id FROM ufs)
                 THEN TRY_CAST({_nullify('uf_provavel_infeccao')} AS SMALLINT)
                 ELSE NULL
            END                                                      AS uf_provavel_infeccao,
            {_mun_fk('municipio_provavel_infeccao')}                 AS municipio_provavel_infeccao,
            CASE WHEN TRY_CAST({_nullify('pais_provavel_infeccao')} AS SMALLINT)
                      IN (SELECT pais_id FROM paises)
                 THEN TRY_CAST({_nullify('pais_provavel_infeccao')} AS SMALLINT)
                 ELSE NULL
            END                                                      AS pais_provavel_infeccao,
            {doenca_case}                                            AS doenca_trabalho,
            {evolucao_case}                                          AS evolucao_caso,
            CASE WHEN notificacao_duplicada IS NULL
                      OR TRIM(notificacao_duplicada) IN ('', '0', '/N')
                 THEN FALSE
                 ELSE TRUE
            END                                                      AS nduplic,
            TRY_CAST({_nullify('fluxo_retorno')} AS SMALLINT)        AS fluxo_retorno,
            TRY_CAST({_nullify('fluxo_recebido')} AS SMALLINT)       AS fluxo_recebido
        FROM zika
    """)
    log.info("notificacoes_casos → %d linhas", conn.execute("SELECT COUNT(*) FROM notificacoes_casos").fetchone()[0])


def _build_obitos_encerrados(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(f"""
        CREATE TABLE obitos AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY row_id) AS obito_id,
            row_id                              AS notificacao_id,
            TRY_CAST({_nullify('data_obito')} AS DATE) AS data_obito
        FROM zika
        WHERE {_nullify('data_obito')} IS NOT NULL
    """)
    log.info("obitos → %d linhas", conn.execute("SELECT COUNT(*) FROM obitos").fetchone()[0])

    conn.execute(f"""
        CREATE TABLE casos_encerrados AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY row_id) AS caso_encerrado_id,
            row_id                              AS notificacao_id,
            TRY_CAST({_nullify('data_encerramento')} AS DATE) AS data_encerramento
        FROM zika
        WHERE {_nullify('data_encerramento')} IS NOT NULL
    """)
    log.info("casos_encerrados → %d linhas", conn.execute("SELECT COUNT(*) FROM casos_encerrados").fetchone()[0])


def _write_parquets(conn: duckdb.DuckDBPyConnection) -> None:
    tables = [
        "ufs", "municipios", "paises", "regionais_saude",
        "unidades_notificadoras", "pacientes",
        "notificacoes_casos", "obitos", "casos_encerrados",
    ]
    for table in tables:
        dest = str(SILVER / f"{table}.parquet").replace("\\", "/")
        conn.execute(f"COPY (SELECT * FROM {table}) TO '{dest}' (FORMAT PARQUET)")
        log.info("Escrito → %s.parquet", table)


def transform() -> None:
    SILVER.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(":memory:")
    try:
        _load_csv(conn)
        _build_ibge_tables(conn)
        _build_paises(conn)
        _build_regionais(conn)
        _build_unidades(conn)
        _build_pacientes(conn)
        _build_notificacoes(conn)
        _build_obitos_encerrados(conn)
        _write_parquets(conn)
        log.info("Transformação concluída → data/silver/")
    finally:
        conn.close()
