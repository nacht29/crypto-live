# Python Code Breakdown

## Constant variables

### AWS configuration
```py
# AWS boto3 config
PIPELINE_IAM_USER = os.getenv("PIPELINE_IAM_USER", "") # boto3 profile
REGION = os.getenv("REGION", "ap-southeast-1") # AWS region
```

- `PIPELINE_IAM_USER`: AWS IAM boto3 profile. This allows you to call AWS services via an IAM user. Note: the `PIPELINE_IAM_USER` is empty by default for it to work in ECS using an attached Service Role, and you have to configure your AWS boto3 profile locally, then export the profile name as an environment variable for the code to work locally. Refer to [this guide here](link-this-to-the-AWS-Guide) to see how to configure your IAM user profiles with its profile credentials via AWS CLI.
- `REGION` The region of your AWS services. See [list of AWS regions and the respective region codes](https://docs.aws.amazon.com/pdfs/global-infrastructure/latest/regions/regions-zones.pdf#aws-regions)

### Data processing metrics

```py
# Data processing
try:
	MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "1000")) # Max size (rows) per microbatch
except ValueError:
	print(f"Invalid MAX_BATCH_SIZE")
	raise(ValueError)

try:
	MAX_BATCH_TIMEOUT = int(os.getenv("MAX_BATCH_TIMEOUT", "10")) # Wait n seconds for input or force flush (batch)
except ValueError:
	print(f"Invalid MAX_BATCH_TIMEOUT")
	raise(ValueError)
```

- `MAX_BATCH_SIZE`: Size of data to microbatch into one JSONL file (in rows).
- `MAX_BATCH_TIMEOUT`: Amount of time (in seconds) before forcing a microbatch flush.

### AWS Services
```py
S3_BUCKET = os.getenv("S3_BUCKET", "crypto-live-bucket") # S3 bucket
S3_JSONL_DIR_PATH = os.getenv("S3_JSONL_DIR_PATH", "batch_jsonl") # S3 bucket directory path to store raw JSONL
BINANCE_WEBSOCKET_SECRET = os.getenv("BINANCE_WEBSOCKET_SECRET", "crypto-live.binance_ws") # Secrets Manager - websocket url
DYNAMO_TABLE_NAME = os.getenv("DYNAMO_TABLE_NAME", "crypto-live-miniticker") # DynamoDB table name
try:
	RETENTION_TTL_DAYS = int(os.getenv("RETENTION_TTL_DAYS", 1)) # Days to retent data in DynamoDB table
except ValueError:
	print("Invalid TTL")
	raise(ValueError)
```

- `S3_BUCKET`: The root path to your S3 bucket (also the bucket name for your S3 objects).
- `S3_JSONL_DIR_PATH`: Directory path in the `S3_BUCKET` to store your objects.
- `BINANCE_WEBSOCKET_SECRET`: Retrieve websocket url endpoints stored in Secrets Manager, mimicking use cases of confidential API endpoint urls.
- `DYNAMO_TABLE_NAME`: DynamoDB table for persisting the formatted miniTicker rows.
- `RETENTION_TTL_DAYS`: DynamoDB TTL retention window (in days). The value is converted to an epoch timestamp and stored as `ttl_days`.

### Async client configuration
```py
# Async Client
TESTNET = bool(os.getenv("TESTNET", True))
```

- `TESTNET`: Enables testnet mode for the Binance websocket client.
	- When set via environment variables, any non-empty string evaluates to `True`.

---

## Dependencies

```py
import os
import signal
import asyncio
import boto3
from binance import AsyncClient, BinanceSocketManager
from datetime import datetime
from time import time
from typing import *
from utils import *
```

- `os`: Read AWS credentials configured in AWS CLI, stored in Environment Variables during local testing.
- `signal`: Handle manual shutdown such as intercepting `Ctrl + C` signals gracefully.
- `asyncio`: Used in all asynchronous functions and procedures.
- `boto3`: Create boto3 sessions to allow user to call AWS services via configured IAM user.
- `binance`: Binance module to connect to the Binance websocket. Refer to this [websocket documentation](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams) by Binance.
- `datetime`: For recording the timestamp of logs.
- `time`: Used for calculating the retention period of objects in DynamoDB. Formula: 
	```
    time + retention_in_days * 24 * 60 * 60 (convert to seconds)
	```
- `typing`: Annotate data types for function headers.
- `utils`: Local Python module containing helper functions. See [utils.py](link-to-utils)

---

## Utility functions (`utils.py`)

### Secrets Manager

```py
def get_secret(session, secret_name:str, region_name:str) -> dict:
```

- Retrieves the Binance websocket secret (JSON string) from AWS Secrets Manager.
- Creates a `secretsmanager` client from the provided boto3 `session`.
- Returns the decoded JSON as a dict (used to fetch the `streams` list).
- Parameters:
	- `session`: boto3 session used to create the Secrets Manager client.
	- `secret_name`: Secret name/ARN/ID to retrieve (configured via `BINANCE_WEBSOCKET_SECRET`).
	- `region_name`: AWS region where the secret is stored (usually `REGION`).

### Raw data transformation

```py
def process_dt_numeric(object:dict, dt_type:str='dt', numeric_str:str='num') -> dict:
```

- Normalizes numeric fields and event time values.
- When `numeric_str='num'`, converts numeric strings to `Decimal` (keeps numeric precision).
- Generates `iso_timestamp` from the `event_time` epoch milliseconds.
	- `dt_type='str'` → `iso_timestamp` as an ISO string.
	- `dt_type='dt'` → `iso_timestamp` as a `datetime` instance.
- Parameters:
	- `object`: Input dict containing at least `event_time` (epoch milliseconds). Typically the output of `format_stream_data()`.
	- `dt_type`: Output type for `iso_timestamp`.
		- `str`: Writes `iso_timestamp` as a string via `strftime("%Y-%m-%dT%H-%M-%S.%fZ")`.
		- `dt`: Writes `iso_timestamp` as a `datetime` instance.
	- `numeric_str`: Controls numeric normalization.
		- `num`: Converts numeric-like strings to `Decimal` (used for DynamoDB).
		- `str`: Keeps all numeric fields as strings (used for JSONL/S3).

```py
def format_stream_data(stream_data:dict) -> dict:
```

- Extracts the Binance miniTicker payload into a cleaner schema.
- Supports both `stream_type` and `stream` keys and raises if missing.
- Returns the normalized dict used downstream by the pipeline.
- Parameters:
	- `stream_data`: Raw websocket message returned by the Binance multiplex socket. Must contain `data` and either `stream` or `stream_type`.

### S3 helpers

```py
def write_jsonl_bytes(batch_data:list[dict]) -> bytes:
```

- Writes a list of dicts into a JSONL-encoded byte buffer.
- Minimizes JSON size with compact separators.
- Parameters:
	- `batch_data`: List of JSON-serializable dicts to write as newline-delimited JSON.

```py
def gzip_file(data:bytes) -> bytes:
```

- Compresses the JSONL bytes payload using gzip for smaller S3 objects.
- Parameters:
	- `data`: Raw (uncompressed) bytes to gzip.

## Main functions

### Session creation

```py
def create_boto3_session(profile:str=None, region:str=None) -> boto3.session:
```

- Creates a boto3 session using the configured AWS profile or default credentials.
- When `profile` is provided, it uses `profile_name=profile` and `region_name=region`.
- Parameters:
	- `profile`: AWS CLI profile name. When falsy (e.g. empty string), boto3 falls back to the default credential chain.
	- `region`: AWS region name (e.g. `ap-southeast-1`).

### Websocket ingestion

```py
async def websocket_ingest(client:AsyncClient, streams:List, dynamo_raw_queue:asyncio.Queue, s3_raw_queue:asyncio.Queue):
```

- Initializes a `BinanceSocketManager` and listens to the multiplexed streams.
- Each incoming message is normalized via `format_stream_data`.
- Pushes:
	- Raw formatted data → `dynamo_raw_queue` (for DynamoDB writes).
	- Stringified numeric/date data → `s3_raw_queue` (for JSONL/S3 output).
- Parameters:
	- `client`: Binance `AsyncClient` created via `AsyncClient.create()`.
	- `streams`: List of websocket stream names passed into `BinanceSocketManager.multiplex_socket(streams)`.
	- `dynamo_raw_queue`: Async queue for rows destined for DynamoDB (consumed by `write_to_dynamodb()`).
	- `s3_raw_queue`: Async queue for rows destined for S3 batching (consumed by `batch_data()`).

### Micro-batching

```py
async def batch_data(raw_queue:asyncio.Queue, batch_queue:asyncio.Queue, max_batch:int, max_timeout:int):
```

- Buffers items from the raw queue into a micro-batch array.
- Flushes the batch when either:
	- `len(buffer)` reaches `max_batch`, or
	- `max_timeout` seconds elapse since the last flush.
- Parameters:
	- `raw_queue`: Async queue providing individual rows (in this pipeline, `s3_raw_queue`).
	- `batch_queue`: Async queue receiving a list of rows per flush (consumed by `write_to_s3()`).
	- `max_batch`: Max number of rows per micro-batch (from `MAX_BATCH_SIZE`).
	- `max_timeout`: Flush timeout window in seconds (from `MAX_BATCH_TIMEOUT`).

### DynamoDB writer

```py
async def write_to_dynamodb(session, raw_queue:asyncio.Queue, concurrency:int=20, ttl_days:int | None = None):
```

- Spawns `concurrency` async tasks to process raw rows.
- Converts numeric fields to `Decimal` and writes to DynamoDB with `UpdateItem`.
- If `ttl_days` is provided, computes TTL epoch time and adds it to the update expression.
- Uses `stream_type` and `iso_timestamp` as the partition/sort key pair.
- Applies an `asyncio.Semaphore` to cap concurrent writes and avoid spikes.
- Parameters:
	- `session`: boto3 session used to create the DynamoDB resource.
	- `raw_queue`: Async queue carrying raw formatted rows (produced by `websocket_ingest()`).
	- `concurrency`: Number of worker tasks spawned for concurrent `UpdateItem` calls.
	- `ttl_days`: Optional TTL retention window (days). When provided, the code computes an epoch timestamp and writes it into `ttl_days`.

### S3 writer

```py
async def write_to_s3(session, batch_queue:asyncio.Queue, bucket:str, bucket_dir:str, filename:str, gzip:bool=True, sse:str | None  = None, sse_kms_key_id:str | None = None):
```

- Reads micro-batches from the queue and writes them to JSONL.
- Optionally gzips and uploads to S3 with additional server-side encryption metadata.
- Generates a timestamped JSONL file under `bucket_dir`.
- Sets `ContentEncoding="gzip"` and `ContentType="application/json"` when gzip is enabled.
- Parameters:
	- `session`: boto3 session used to create the S3 client.
	- `batch_queue`: Async queue carrying micro-batches (list of dicts) from `batch_data()`.
	- `bucket`: Target S3 bucket name.
	- `bucket_dir`: S3 prefix/folder under the bucket to write objects into (e.g. `batch_jsonl`).
	- `filename`: Base filename used to build the object key. The code strips the `.jsonl` suffix if present.
	- `gzip`: When `True`, compresses the JSONL payload and sets `ContentEncoding="gzip"`.
	- `sse`: Optional server-side encryption setting (e.g. `AES256` or `aws:kms`).
	- `sse_kms_key_id`: Optional KMS Key ID/ARN when using KMS encryption.

### Pipeline entrypoint

```py
async def main(load_s3:bool=True, load_dynamod:bool=True):
```

- Creates the boto3 session and loads the Binance websocket secret.
- Initializes:
	- async queues (raw, batch),
	- websocket ingestion,
	- batcher,
	- optional writers for S3 and DynamoDB.
- Handles graceful shutdown via `SIGINT`/`SIGTERM`, cancels tasks, and closes the Binance client.
- Toggles output sinks using `load_s3` and `load_dynamod`.
- Parameters:
	- `load_s3`: When `True`, starts the S3 sink task via `write_to_s3()`.
	- `load_dynamod`: When `True`, starts the DynamoDB sink task via `write_to_dynamodb()`.

## Execution sequence

### Overview

```text
pipeline.py (__main__)
└─ asyncio.run(main(load_s3=True, load_dynamod=True))
   ├─ create_boto3_session(profile=PIPELINE_IAM_USER, region=REGION)
   ├─ get_secret(session, BINANCE_WEBSOCKET_SECRET, REGION) -> streams
   ├─ AsyncClient.create(testnet=TESTNET)
   └─ asyncio.create_task(...)
      ├─ websocket_ingest(...) -> format_stream_data(...) -> process_dt_numeric(..., dt_type="str", numeric_str="str")
      ├─ batch_data(...)
      ├─ (if load_s3) write_to_s3(...) -> write_jsonl_bytes(...) -> gzip_file(...)
      └─ (if load_dynamod) write_to_dynamodb(...) -> process_dt_numeric(..., dt_type="str", numeric_str="num")
```

- Note: all tasks run concurrently. The steps below are the logical sequence of what is initialized and how data flows between tasks.

### Sequence details

1. Initialisation
	- Read environment variables and constantsy:
		- `PIPELINE_IAM_USER`, `REGION`, `MAX_BATCH_SIZE`, `MAX_BATCH_TIMEOUT`
		- `S3_BUCKET`, `S3_JSONL_DIR_PATH`, `BINANCE_WEBSOCKET_SECRET`, `DYNAMO_TABLE_NAME`, `RETENTION_TTL_DAYS`
		- `TESTNET`
	- `MAX_BATCH_SIZE` and `MAX_BATCH_TIMEOUT` are cast to `int` and raise `ValueError` if invalid.

2. Script execution
	- The script starts the event loop via:
		```py
		asyncio.run(main(load_s3=True, load_dynamod=True))
		```

3. `main()` setup
	- Creates AWS session:
		- `session = create_boto3_session(profile=PIPELINE_IAM_USER, region=REGION)`
	- Loads websocket configuration:
		- `secret = get_secret(session, BINANCE_WEBSOCKET_SECRET, REGION)`
		- `streams = secret["streams"]`
	- Creates the Binance websocket client:
		- `client = await AsyncClient.create(testnet=TESTNET)`
	- Creates queues:
		- `dynamo_raw_queue`: raw formatted rows to DynamoDB
		- `s3_raw_queue`: raw rows to be micro-batched for S3
		- `batch_queue`: micro-batches (list of rows) to be uploaded to S3

4. Task orchestration
	- Starts the core pipeline tasks:
		- `asyncio.create_task(websocket_ingest(client, streams, dynamo_raw_queue, s3_raw_queue))`
		- `asyncio.create_task(batch_data(s3_raw_queue, batch_queue, MAX_BATCH_SIZE, MAX_BATCH_TIMEOUT))`
	- Starts optional sinks:
		- S3 sink: `asyncio.create_task(write_to_s3(session, batch_queue, S3_BUCKET, S3_JSONL_DIR_PATH, filename="miniticker", gzip=True))` when `load_s3=True`
		- DynamoDB sink: `asyncio.create_task(write_to_dynamodb(session, dynamo_raw_queue, ttl_days=RETENTION_TTL_DAYS))` when `load_dynamod=True`

5. Per-message ingestion (`websocket_ingest()`)
	- Receives a websocket message and normalizes it:
		- `formatted_data = format_stream_data(stream_data)`
	- Fan-out to both sinks:
		- DynamoDB path: `await dynamo_raw_queue.put(formatted_data)`
		- S3 path: `await s3_raw_queue.put(process_dt_numeric(formatted_data, dt_type="str", numeric_str="str"))`

6. DynamoDB sink (`write_to_dynamodb()`)
	- Spawns `concurrency` workers; each worker:
		- `raw = await dynamo_raw_queue.get()`
		- `row = process_dt_numeric(raw, dt_type="str", numeric_str="num")` (adds `iso_timestamp`, converts numeric strings → `Decimal`)
		- Calls `table.update_item(...)` inside `asyncio.to_thread(...)` (boto3 is sync / blocking).
		- Calls `dynamo_raw_queue.task_done()` after processing.

7. S3 sink (`batch_data()` + `write_to_s3()`)
	- `batch_data()` reads rows from `s3_raw_queue` and flushes to `batch_queue` on:
		- size threshold (`MAX_BATCH_SIZE`), or
		- time threshold (`MAX_BATCH_TIMEOUT`).
	- `write_to_s3()` reads a micro-batch from `batch_queue` and:
		- `file_body = write_jsonl_bytes(batch_data)`
		- `file_body = gzip_file(file_body)` when `gzip=True`
		- Calls `s3_client.put_object(...)` inside `asyncio.to_thread(...)`.
		- Calls `batch_queue.task_done()` after upload.

8. Shutdown handling
	- `main()` registers `SIGINT`/`SIGTERM` handlers that set an `asyncio.Event`.
	- When the event is set, the pipeline cancels all running tasks and then closes the Binance client connection (`client.close_connection()`).
