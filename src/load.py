"""Persistencia da camada Raw, localmente e no Google Cloud Storage."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from google.cloud import storage
import polars as pl


LOGGER = logging.getLogger(__name__)


def save_raw_payments(df: pl.DataFrame, output_path: Path) -> Path:
    """Grava o resultado da extracao em Parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(output_path, compression="zstd")
    LOGGER.info("Arquivo Raw salvo: %s | total: %s linhas", output_path, df.height)
    return output_path


def upload_raw_to_gcs(local_file: Path, bucket_name: str) -> str:
    """Envia o Parquet ao bucket usando a Service Account do ambiente."""
    extracted_at = datetime.now(timezone.utc)
    object_name = f"raw/payment_{extracted_at:%Y-%m-%d}.parquet"

    blob = storage.Client().bucket(bucket_name).blob(object_name)
    blob.upload_from_filename(local_file, content_type="application/octet-stream")

    gcs_uri = f"gs://{bucket_name}/{object_name}"
    LOGGER.info("Arquivo enviado ao Cloud Storage: %s", gcs_uri)
    return gcs_uri
