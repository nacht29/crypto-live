# crypto-live

Data pipeline and visualisation for popular cryptocurrency exchange rates.

## Project overview

The project ingests Binance mini-ticker market data in real time, persists the
raw stream in AWS, and prepares curated parquet datasets for downstream
analytics and dashboards. The core runtime is an asyncio-based Python
application that manages ingestion, batching, persistence, and graceful
shutdown handling.

<!-- TODO: Add an architecture diagram that shows the flow between Binance, the
pipeline container, DynamoDB, S3, Glue, and the visualisation layer. -->

## Repository layout

| Path | Description |
| --- | --- |
| `src/main/pipeline.py` | Orchestrates websocket ingestion, batching, and writes to DynamoDB and S3. |
| `src/main/utils.py` | Helper utilities for AWS Secrets Manager, numeric/date conversion, and file helpers. |
| `src/glue/parquet.py` | AWS Glue job that loads raw JSONL batches and writes partitioned Parquet to S3. |
| `set-up/dependencies.sh` | Convenience script that installs Python dependencies with `pip`. |
| `set-up/makefile.sh` | Example shell script showing how credentials were exported for local testing. |
| `permissions/GlueServiceRole-crypto-live/` | IAM inline policy JSON documents for the Glue service role. |

<!-- TODO: Replace `set-up/makefile.sh` with a safer example that uses
placeholder credentials and clarify how to manage secrets securely. -->

## Data flow

1. **Secrets retrieval** – `create_boto3_session` creates a boto3 session using
a named profile (`crypto-live-pipeline01`). `get_secret` fetches Binance stream
configuration from AWS Secrets Manager (`crypto-live.binance_ws`).
2. **Websocket ingestion** – `websocket_ingest` opens a Binance multiplex
socket and forwards formatted mini-ticker payloads to in-memory queues.
3. **Batching** – `batch_data` accumulates messages from the S3 queue. It
flushes once the batch reaches `MAX_BATCH_SIZE` (default 1,000) or when the
`MAX_BATCH_TIMEOUT` (default 10 seconds) elapses.
4. **S3 persistence** – `write_to_s3` converts batches to newline-delimited
JSON, optionally gzips them, and uploads files to `s3://crypto-live-bucket/
batch_jsonl/` with timestamped keys.
5. **DynamoDB persistence** – `write_to_dynamodb` upserts each event into the
`crypto-live-miniticker` table, converting numeric fields to `Decimal` and
stamping TTL metadata when configured.
6. **Glue ETL** – The Glue job in `src/glue/parquet.py` reads raw batches via
the Glue Data Catalog and writes Snappy-compressed Parquet files partitioned by
stream and symbol.

## Prerequisites

* Python 3.10+
* AWS account with access to Secrets Manager, DynamoDB, S3, Glue, and CloudWatch
  Logs
* Binance API testnet access (websocket streams)
* Configured AWS CLI profile for `crypto-live-pipeline01`

Install the Python dependencies locally:

```bash
pip install --upgrade python-binance boto3 botocore pandas numpy colorama
```

Alternatively run the helper script:

```bash
bash set-up/dependencies.sh
```

<!-- TODO: Document the recommended virtual environment strategy (e.g. pyenv,
conda, or Poetry) for local development. -->

## AWS infrastructure requirements

* **S3 bucket** – `crypto-live-bucket` with subfolders `batch_jsonl/` (raw) and
  `parquet/` (curated). Server-side encryption is supported via the optional
  `sse`/`sse_kms_key_id` parameters in `write_to_s3`.
* **DynamoDB table** – `crypto-live-miniticker` with partition key
  `stream_type` and sort key `iso_timestamp`. TTL can be enabled on the
  `ttl_days` attribute.
* **Secrets Manager secret** – `crypto-live.binance_ws` storing a JSON object
  with a `streams` list (Binance websocket stream identifiers).
* **Glue Data Catalog** – Database `crypto_live_db` with table `raw_batch_jsonl`
  pointing to the raw JSONL S3 location.
* **Glue job** – Executes `src/glue/parquet.py` with the service role granted
  read access to the catalog and S3, as captured in
  `permissions/GlueServiceRole-crypto-live/`.

<!-- TODO: Expand with step-by-step provisioning instructions for each AWS
resource (console + Terraform/CloudFormation guidance). -->

## Configuration

The ingestion service uses module-level constants in `src/main/pipeline.py` to
control runtime behaviour:

* `REGION`, `PIPELINE_IAM_USER`, and `BINANCE_WEBSOCKET_SECRET_NAME` determine
  how AWS sessions and secrets are resolved.
* `MAX_BATCH_SIZE`, `MAX_BATCH_TIMEOUT`, and queue sizes tune throughput and
  memory usage.
* `RETENTION_TTL_DAYS` controls the TTL value written to DynamoDB (set to 1 day
  by default).
* `BATCH_JSONL_BUCKET_DIR` and `BUCKET` define S3 storage layout.

Override these by parameterising the script or using environment variables when
packaging for production.

<!-- TODO: Decide on the final configuration mechanism (env vars, config file,
or CLI arguments) before productionising. -->

## Running the ingestion pipeline locally

1. Ensure the AWS CLI profile `crypto-live-pipeline01` is configured with
   programmatic access credentials that can assume the required IAM roles.
2. Populate Secrets Manager with a `streams` array (e.g.
   `["btcusdt@miniTicker", "ethusdt@miniTicker"]`).
3. Launch the async runtime:

   ```bash
   python -m src.main.pipeline
   ```

4. Press `Ctrl+C` to trigger the graceful shutdown handler. The coroutine tasks
   are cancelled, in-flight writes finish, and the Binance client connection is
   closed.

Batches will appear in `s3://crypto-live-bucket/batch_jsonl/` (gzip files by
default) and DynamoDB will contain up-to-date ticker snapshots keyed by stream
and timestamp.

<!-- TODO: Capture runtime logs and metrics expectations (e.g. CloudWatch log
streams, custom metrics) for operations playbooks. -->

## Running the Glue conversion job

1. Package `src/glue/parquet.py` into a Glue job script or upload to an S3 path
   referenced by the job.
2. Configure the job to use the Glue Data Catalog database `crypto_live_db` and
   table `raw_batch_jsonl`.
3. Grant the Glue service role the policies in
   `permissions/GlueServiceRole-crypto-live/`.
4. Schedule the job (e.g. hourly) to convert new JSONL batches to Parquet in
   `s3://crypto-live-bucket/parquet/`, partitioned by `stream` and `symbol`.

<!-- TODO: Add screenshots from the AWS Glue console showing the job settings
and successful run history. -->

## Data model

Mini-ticker payloads are normalised to the following schema before persistence:

| Field | Type | Description |
| --- | --- | --- |
| `event_type` | `str` | Binance stream event type (e.g. `24hrMiniTicker`). |
| `event_time` | `int` (ms) | Event timestamp in epoch milliseconds. |
| `stream_type` | `str` | Stream identifier (e.g. `btcusdt@miniTicker`). |
| `symbol` | `str` | Trading pair symbol. |
| `close_price` | `Decimal` | Last price. |
| `open_price` | `Decimal` | Price 24 hours ago. |
| `high_price` | `Decimal` | Highest price over the trailing window. |
| `low_price` | `Decimal` | Lowest price over the trailing window. |
| `total_traded_volume` | `Decimal` | Total traded volume in the base asset. |
| `total_traded_base_asset_volume` | `Decimal` | Total traded quote asset volume. |
| `iso_timestamp` | `str` or `datetime` | ISO-8601 timestamp derived from `event_time`. |
| `ttl_days` | `int` | Optional attribute controlling DynamoDB TTL. |

`process_dt_numeric` can emit string or datetime objects for `iso_timestamp`
and convert numeric strings to `Decimal` for DynamoDB compatibility.

## Operational considerations

* **Concurrency controls** – DynamoDB writes are throttled with an asyncio
  semaphore (default concurrency of 20) to avoid exceeding provisioned
  throughput.
* **Backpressure** – Queue sizes can be tuned to prevent memory growth during
  spikes.
* **Compression** – Gzip reduces S3 storage costs and improves Glue job input
  performance.
* **Graceful shutdown** – `signal.SIGINT`/`SIGTERM` handlers ensure tasks cancel
  cleanly and resources close properly.

<!-- TODO: Align on alerting thresholds (e.g. DynamoDB throttles, S3 error
rates) and integrate with the team's monitoring stack. -->

## Next steps

* Containerise the ingestion service and deploy via ECS/Fargate or EKS.
* Automate infrastructure provisioning with IaC.
* Build dashboards that read the Parquet dataset and surface real-time
  analytics.

<!-- TODO: Provide guidance on the target visualisation stack and embed sample
screenshots once available. -->
