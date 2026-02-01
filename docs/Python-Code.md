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
- `MAX_BATCH_TIMEOUT`: Amount of time (in seconds) before forcing a mircobatch to avoid long timeouts.

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

- `S3_BUCKET`: The root path to your S3 bucket (which is also the bucket name for your S3 objects).
- `S3_JSONL_DIR_PATH`: Directory path in the `S3_BUCKET` to store your objects.
- `BINANCE_WEBSOCKET_SECRET`: Retrieve websocket url endpoints stored in Secrets Manager, mimicking use cases of confidential API endpoint urls.
- `DYNAMO_TABLE_NAME`: ``

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

- `os`: Read AWS credentiuals configured in AWS CLI, stored in Environment Variables during local testing.
- `signal`: Handle manual shutdown such as intercepting `Ctrl + C` signals gracefully.
- `asyncio`: Used in all asynchronous functions and procedures.
- `boto3`: Create boto3 sessions to allow user to call AWS services via configured IAM user.
- `binance`: Binance module to connect to the Binance websocket. Refer to this [websocket documentation](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams) by Binance.
- `datetime`: For recording the timestamp of logs.
- `time`: Used for calculating the retention period of objects in DynamoDB. Formula: 
	```
    time + retention_in_days * 24 * 60 * 60 (convert to seconds)
	```
- `typing`: Anotate data type for function headers.
- `utils`: Local Python module containing helper functions. See [utils.py](link-to-utils)

---

## Utility functions (`utils.py`)

## Main functions

## Execution sequence

