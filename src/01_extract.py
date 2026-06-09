import requests
import io
import logging
from zipfile import ZipFile
from pathlib import Path

BRONZE = Path(__file__).resolve().parent.parent / "data" / "bronze"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

_IBGE_URL = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio"
    "/estrutura_territorial/divisao_territorial/2025/DTB_2025.zip"
)
_IBGE_FILE = "RELATORIO_DTB_BRASIL_2025_MUNICIPIOS.xls"


def get_ibge_data() -> None:
    dest = BRONZE / _IBGE_FILE
    if dest.exists():
        log.info("Já existe, pulando → %s", dest.name)
        return

    log.info("Baixando DTB 2025 do IBGE...")
    response = requests.get(_IBGE_URL, timeout=60)
    response.raise_for_status()

    with ZipFile(io.BytesIO(response.content)) as zf:
        zf.extract(_IBGE_FILE, BRONZE)

    log.info("Extraído → %s", dest.name)
