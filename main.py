"""Ponto de entrada da ingestao Chicago Payments.

Exponha ``ingest_payments`` como entry point ao publicar uma Cloud Run Function.
O mesmo arquivo tambem pode ser executado localmente para testes.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.Extract import extract_payments
from src.load import save_raw_payments, upload_raw_to_gcs


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_RAW_FILE_PATH = PROJECT_ROOT / "data" / "raw" / "payments.parquet"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_raw_file_path() -> Path:
    """Usa /tmp no Cloud Run e data/raw durante a execucao local."""
    is_cloud_run = bool(os.getenv("K_SERVICE"))
    default_path = "/tmp/payments.parquet" if is_cloud_run else DEFAULT_RAW_FILE_PATH
    return Path(os.getenv("LOCAL_RAW_FILE_PATH", default_path))


def run_ingestion() -> dict[str, str | int]:
    """Extrai pagamentos, grava Parquet e envia o arquivo para o Cloud Storage."""
    configure_logging()

    payments = extract_payments()
    local_file = save_raw_payments(payments, get_raw_file_path())

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if bucket_name:
        gcs_uri = upload_raw_to_gcs(local_file, bucket_name)
        return {"status": "success", "rows": payments.height, "gcs_uri": gcs_uri}

    if os.getenv("K_SERVICE"):
        raise RuntimeError("GCS_BUCKET_NAME deve ser configurada na Cloud Run Function.")

    logging.getLogger(__name__).warning(
        "GCS_BUCKET_NAME nao configurada; upload para Cloud Storage ignorado."
    )
    return {"status": "success", "rows": payments.height, "local_file": str(local_file)}


def ingest_payments(request: object) -> tuple[dict[str, str | int], int]:
    """Função HTTP chamada pelo Cloud Scheduler.

    O objeto ``request`` é recebido pelo runtime; ele não é usado pois a
    ingestão não aceita parâmetros externos nesta primeira versão.
    """
    del request
    try:
        result = run_ingestion()
        return result, 200
    except Exception:
        logging.getLogger(__name__).exception("Falha na ingestao de pagamentos.")
        return {"status": "error", "message": "Falha na ingestao. Consulte o Cloud Logging."}, 500


def main() -> None:
    """Executa a mesma ingestão diretamente, para desenvolvimento local."""
    result = run_ingestion()
    logging.getLogger(__name__).info("Ingestao finalizada: %s", result)


if __name__ == "__main__":
    main()
