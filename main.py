"""Ponto de entrada do Job de ingestao Chicago Payments."""

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
    default_path = "/tmp/payments.parquet" if os.getenv("CLOUD_RUN_JOB") else DEFAULT_RAW_FILE_PATH
    return Path(os.getenv("LOCAL_RAW_FILE_PATH", default_path))


def main() -> None:
    configure_logging()

    payments = extract_payments()
    local_file = save_raw_payments(payments, get_raw_file_path())

    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if bucket_name:
        upload_raw_to_gcs(local_file, bucket_name)
    elif os.getenv("CLOUD_RUN_JOB"):
        raise RuntimeError("GCS_BUCKET_NAME deve ser configurada no Cloud Run Job.")
    else:
        logging.getLogger(__name__).warning(
            "GCS_BUCKET_NAME nao configurada; upload para Cloud Storage ignorado."
        )


if __name__ == "__main__":
    main()
