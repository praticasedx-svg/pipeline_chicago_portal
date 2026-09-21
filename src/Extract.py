import os
import logging

import polars as pl
import requests as rs

API_URL = "https://data.cityofchicago.org/api/v3/views/s4vu-giwb/query.json"
PAGE_SIZE = 5_000
LOGGER = logging.getLogger(__name__)

def extract_payments() -> pl.DataFrame:
    app_token = os.getenv("SOCRATA_APP_TOKEN")
    if not app_token:
        raise RuntimeError("SOCRATA_APP_TOKEN nao foi configurada.")

    page_number = 1
    processed_rows = 0
    batches: list[pl.DataFrame] = []

    headers = {
        "X-App-Token": app_token,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "chicago-payments-pipeline/0.1",
    }

    with rs.Session() as session:
        while True:
            payload = {
                "query": """
                    SELECT
                        *,
                        :id AS source_row_id
                    ORDER BY :id
                """,
                "page": {
                    "pageNumber": page_number,
                    "pageSize": PAGE_SIZE,
                },
                "includeSynthetic": False,
            }

            response = session.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            rows = response.json()

            if not rows:
                break

            batch = pl.DataFrame(rows, strict=False)
            batches.append(batch)
            processed_rows += batch.height

            LOGGER.info(
                "Pagina %s concluida | lote: %s linhas | total: %s linhas",
                page_number,
                batch.height,
                processed_rows,
            )

            if len(rows) < PAGE_SIZE:
                break

            page_number += 1

    if not batches:
        raise RuntimeError("A API nao retornou nenhum pagamento.")

    return pl.concat(batches, how="diagonal_relaxed")
