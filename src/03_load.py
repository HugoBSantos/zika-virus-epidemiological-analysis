import io
import logging
import os
from pathlib import Path

import polars as pl
import psycopg
from dotenv import load_dotenv

SILVER = Path(__file__).resolve().parent.parent / "data" / "silver"
_SQL_DDL = Path(__file__).resolve().parent.parent / "sql" / "ddl" / "silver.sql"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# FK-safe insertion order: parents before children
_LOAD_ORDER = [
    "ufs",
    "paises",
    "municipios",
    "regionais_saude",
    "unidades_notificadoras",
    "pacientes",
    "notificacoes_casos",
    "obitos",
    "casos_encerrados",
]


def _run_ddl(conn: psycopg.Connection) -> None:
    sql = _SQL_DDL.read_text(encoding="utf-8")
    for stmt in (s.strip() for s in sql.split(";")):
        if stmt:
            conn.execute(stmt)
    log.info("DDL executado → silver.sql")


def _copy_table(conn: psycopg.Connection, table: str) -> None:
    df = pl.read_parquet(SILVER / f"{table}.parquet")
    cols = ", ".join(df.columns)

    buf = io.StringIO()
    df.write_csv(buf, null_value="")
    buf.seek(0)

    with conn.cursor() as cur:
        with cur.copy(
            f"COPY silver.{table} ({cols}) FROM STDIN "
            f"(FORMAT CSV, HEADER TRUE, NULL '')"
        ) as copy:
            copy.write(buf.read())

    log.info("%-25s → %d linhas", table, len(df))


def load() -> None:
    load_dotenv()
    url = os.environ["POSTGRES_URL"]

    with psycopg.connect(url) as conn:
        _run_ddl(conn)
        for table in _LOAD_ORDER:
            _copy_table(conn, table)

    log.info("Carga concluída → PostgreSQL")
