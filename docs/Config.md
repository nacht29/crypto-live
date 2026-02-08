# Configuration & Setup

This document covers prerequisites, local installation, AWS resource requirements, and runtime configuration for the ingestion pipeline.

## Prerequisites

- Python 3.10+
- AWS account access to: Secrets Manager, DynamoDB, S3 (and optionally Glue + CloudWatch Logs)
- AWS credentials available locally (AWS CLI profile or default credential chain)
- Binance websocket stream names to ingest (typically via testnet while developing)

## Local installation

1. Create and activate a virtual environment:

	 ```bash
	 python3 -m venv myvenv
	 source myvenv/bin/activate
	 ```

2. Install Python dependencies:

	 ```bash
	 python -m pip install --upgrade -r set-up/requirements.txt
	 ```

## AWS resources

The pipeline expects the following resources. The resource names below are the defaults used in [`src/main/pipeline.py`](https://github.com/nacht29/crypto-live/blob/main/src/main/pipeline.py) and [`src/main/utils.py`](https://github.com/nacht29/crypto-live/blob/main/src/main/utils.py):

- **S3 bucket**: `crypto-live-bucket`
	- Raw micro-batches prefix: `batch_jsonl/` (default `S3_JSONL_DIR_PATH`)
	- Curated dataset (Parquet) prefix: `parquet/` (convention; Glue script/config dependent)
- **DynamoDB table**: `crypto-live-miniticker`
	- Partition key: `stream_type`
	- Sort key: `iso_timestamp`
	- Optional TTL attribute: `ttl_days`
- **Secrets Manager secret**: `crypto-live.binance_ws`
	- JSON payload with a `streams` list, for example:
		```json
		{ "streams": ["btcusdt@miniTicker", "ethusdt@miniTicker"] }
		```
- **(Optional) Glue**
	- Data Catalog database/table pointing at the raw JSONL S3 prefix
	- Glue job script to convert S3 JSONL files to Parquet. See [`src/glue/parquet.py`](https://github.com/nacht29/crypto-live/blob/main/src/glue/parquet.py)

More AWS setup notes live in `docs/AWS.md` (WIP).

## Runtime configuration (environment variables)

These variables are read by `src/main/pipeline.py`:

### AWS session

- `PIPELINE_IAM_USER` (default: empty) — AWS CLI profile name to use locally (example: `crypto-live-pipeline01`). When empty, boto3 falls back to the default credential chain.
- `REGION` (default: `ap-southeast-1`) — AWS region for Secrets Manager/DynamoDB/S3.

### Batching / retention

- `MAX_BATCH_SIZE` (default: `1000`) — max rows per S3 micro-batch.
- `MAX_BATCH_TIMEOUT` (default: `10`) — seconds before forcing a micro-batch flush.
- `RETENTION_TTL_DAYS` (default: `1`) — DynamoDB retention window (days), written as an epoch timestamp in `ttl_days`.

### AWS resource names

- `S3_BUCKET` (default: `crypto-live-bucket`)
- `S3_JSONL_DIR_PATH` (default: `batch_jsonl`)
- `BINANCE_WEBSOCKET_SECRET` (default: `crypto-live.binance_ws`)
- `DYNAMO_TABLE_NAME` (default: `crypto-live-miniticker`)

### Binance client

- `TESTNET` (default: `True`) — enables Binance testnet mode. Note: in Python, any non-empty string value will evaluate to `True` with the current `bool(os.getenv(...))` implementation.

## Container logging (recommended)

For ECS/Docker, write logs to stdout/stderr and run Python unbuffered.
This repo’s `Dockerfile` sets:

- `PYTHONUNBUFFERED=1`
- `PYTHONIOENCODING=utf-8`

## Running locally

1. Ensure AWS credentials are available (either set `PIPELINE_IAM_USER` to an AWS CLI profile name, or rely on the default credential chain).
2. Ensure the Secrets Manager secret referenced by `BINANCE_WEBSOCKET_SECRET` exists and contains a `streams` list.
3. Run the pipeline:

	 ```bash
	 python -m src.main.pipeline
	 ```

4. Stop with `Ctrl+C` (SIGINT). The pipeline cancels tasks and closes the Binance connection.

Expected outputs:

- S3 JSONL batches under `s3://$S3_BUCKET/$S3_JSONL_DIR_PATH/` (gzip enabled by default)
- DynamoDB rows in `$DYNAMO_TABLE_NAME` keyed by `stream_type` and `iso_timestamp`

## Running the Glue conversion job (optional)

1. Create/configure a Glue job using `src/glue/parquet.py`.
2. Point it at the raw JSONL S3 prefix and write partitioned Parquet to your target S3 prefix.
3. Grant the Glue service role the required S3 and Glue Data Catalog permissions (see `permissions/`).
