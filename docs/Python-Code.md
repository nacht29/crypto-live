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

### Raw data transformation

```py
def process_dt_numeric(object:dict, dt_type:str='dt', numeric_str:str='num') -> dict:
```

- Normalizes numeric fields and event time values.
- When `numeric_str='num'`, converts numeric strings to `Decimal` (keeps numeric precision).
- Generates `iso_timestamp` from the `event_time` epoch milliseconds.
	- `dt_type='str'` → `iso_timestamp` as an ISO string.
	- `dt_type='dt'` → `iso_timestamp` as a `datetime` instance.

```py
def format_stream_data(stream_data:dict) -> dict:
```

- Extracts the Binance miniTicker payload into a cleaner schema.
- Supports both `stream_type` and `stream` keys and raises if missing.
- Returns the normalized dict used downstream by the pipeline.

### S3 helpers

```py
def write_jsonl_bytes(batch_data:list[dict]) -> bytes:
```

- Writes a list of dicts into a JSONL-encoded byte buffer.
- Minimizes JSON size with compact separators.

```py
def gzip_file(data:bytes) -> bytes:
```

- Compresses the JSONL bytes payload using gzip for smaller S3 objects.

## Main functions

### Session creation

```py
def create_boto3_session(profile:str=None, region:str=None) -> boto3.session:
```

- Creates a boto3 session using the configured AWS profile or default credentials.
- When `profile` is provided, it uses `profile_name=profile` and `region_name=region`.

### Websocket ingestion

```py
async def websocket_ingest(client:AsyncClient, streams:List, dynamo_raw_queue:asyncio.Queue, s3_raw_queue:asyncio.Queue):
```

- Initializes a `BinanceSocketManager` and listens to the multiplexed streams.
- Each incoming message is normalized via `format_stream_data`.
- Pushes:
	- Raw formatted data → `dynamo_raw_queue` (for DynamoDB writes).
	- Stringified numeric/date data → `s3_raw_queue` (for JSONL/S3 output).

### Micro-batching

```py
async def batch_data(raw_queue:asyncio.Queue, batch_queue:asyncio.Queue, max_batch:int, max_timeout:int):
```

- Buffers items from the raw queue into a micro-batch array.
- Flushes the batch when either:
	- `len(buffer)` reaches `max_batch`, or
	- `max_timeout` seconds elapse since the last flush.

### DynamoDB writer

```py
async def write_to_dynamodb(session, raw_queue:asyncio.Queue, concurrency:int=20, ttl_days:int | None = None):
```

- Spawns `concurrency` async tasks to process raw rows.
- Converts numeric fields to `Decimal` and writes to DynamoDB with `UpdateItem`.
- If `ttl_days` is provided, computes TTL epoch time and adds it to the update expression.
- Uses `stream_type` and `iso_timestamp` as the partition/sort key pair.
- Applies an `asyncio.Semaphore` to cap concurrent writes and avoid spikes.

### S3 writer

```py
async def write_to_s3(session, batch_queue:asyncio.Queue, bucket:str, bucket_dir:str, filename:str, gzip:bool=True, sse:str | None  = None, sse_kms_key_id:str | None = None):
```

- Reads micro-batches from the queue and writes them to JSONL.
- Optionally gzips and uploads to S3 with additional server-side encryption metadata.
- Generates a timestamped JSONL file under `bucket_dir`.
- Sets `ContentEncoding="gzip"` and `ContentType="application/json"` when gzip is enabled.

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

## Execution sequence

1. Read environment variables for AWS config, batch sizing, and service names.
2. Create a boto3 session and fetch the secret containing Binance stream names.
3. Start the websocket ingestion task to stream miniTicker data.
4. Start the batcher to accumulate JSONL chunks for S3.
5. If enabled, write:
	- raw rows to DynamoDB,
	- micro-batches to S3 as compressed JSONL objects.
6. On shutdown, cancel tasks and close the websocket client connection.
