# Chicago Payments — ingestão Raw

Job de ingestão da API pública **Chicago Payments**. O processo pagina os pagamentos, gera um Parquet temporário e o envia ao Google Cloud Storage.

## Fluxo

```text
Chicago Data Portal API → /tmp/payments.parquet → gs://<bucket>/raw/payments/extracted_at=AAAA-MM-DD/
```

## Configuração local

Crie um arquivo `.env` na raiz do projeto:

```text
SOCRATA_APP_TOKEN=seu_app_token
GCS_BUCKET_NAME=nome-do-seu-bucket
```

Rode localmente:

```powershell
uv run python -m src.extract
```

Sem `GCS_BUCKET_NAME`, o Parquet permanece em `data/raw/payments.parquet` e o upload é ignorado.

## Cloud Run Job

Use um bucket com hífens, não sublinhado: `dados-chicago-<identificador-unico>`. O nome `dados_chicago` é inválido no Cloud Storage.

No Cloud Run, `LOCAL_RAW_FILE_PATH` aponta para `/tmp/payments.parquet`; esse arquivo é temporário. A Service Account associada ao Job deve ter, no mínimo, o papel `roles/storage.objectCreator` no bucket. O token Socrata deve ser injetado por Secret Manager como `SOCRATA_APP_TOKEN`.

O container é executado como Job, não como Service, pois o processo tem início, fim e não expõe HTTP.
# pipeline_chicago_portal
