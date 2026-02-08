# crypto-live
Data pipeline and visualisation for popular cryptocurrency exchange rates.

## Project overview

The project ingests Binance mini-ticker market data in real time, persists the
raw stream in AWS DynamoDB, and prepares curated Parquet datasets for storage and analytics.

At its core, the project uses an asyncio-based Python application that manages ingestion, batching, persistence, and graceful shutdown handling.

---

<!-- TODO: Add an architecture diagram that shows the flow between Binance, the
pipeline container, DynamoDB, S3, Glue, and the visualisation layer. -->

## How it works (high level)

1. Read stream configuration from AWS Secrets Manager.
2. Connect to Binance websocket streams and ingest mini-ticker events.
3. Fan out to:
   - DynamoDB for up-to-date ticker snapshots (with optional TTL).
   - S3 for micro-batched JSONL files (optionally gzip).
4. Optionally run an AWS Glue job to convert raw JSONL batches into partitioned Parquet.

## Repository layout

| Path | Description |
| --- | --- |
| `src/main/pipeline.py` | Orchestrates websocket ingestion, batching, and writes to DynamoDB and S3. |
| `src/main/utils.py` | Helper utilities for AWS Secrets Manager, numeric/date conversion, and file helpers. |
| `src/glue/parquet.py` | AWS Glue job that loads raw JSONL batches and writes partitioned Parquet to S3. |
| `set-up/requirements.txt` | List of Python dependencies to be installed via `pip`. |
| `permissions/*` | IAM inline policy in JSON for the service roles needed for the pipeline. |

---

## Documentation

- `docs/Config.md` — prerequisites, installation, AWS resources, environment variables, and how to run locally.
- `docs/AWS.md` — AWS provisioning notes (WIP).
- `docs/Python-Code.md` — code walkthrough for the ingestion pipeline.

## Next steps

* Containerise the ingestion service and deploy via ECS/Fargate or EKS.
* Automate infrastructure provisioning with IaC.
* Build dashboards that read the Parquet dataset and surface real-time
  analytics.

<!-- TODO: Provide guidance on the target visualisation stack and embed sample
screenshots once available. -->
