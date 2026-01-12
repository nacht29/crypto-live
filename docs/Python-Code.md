# Python Code Breakdown

## Constant variables

### AWS configuration
```py
# AWS constants
PIPELINE_IAM_USER = os.getenv("PIPELINE_IAM_USER", "")
REGION = os.getenv("REGION", "ap-southeast-1")
BUCKET = os.getenv("BUCKET", "crypto-live-bucket")
BATCH_JSONL_BUCKET_DIR = os.getenv("BATCH_JSONL_BUCKET_DIR", "batch_jsonl")
BINANCE_WEBSOCKET_SECRET_NAME = os.getenv("BINANCE_WEBSOCKET_SECRET_NAME", "crypto-live.binance_ws")
```

- `PIPELINE_IAM_USER`: AWS IAM boto3 profile. This allows you to call AWS services via an IAM user. Note: the `PIPELINE_IAM_USER` is empty by default for it to work in ECS using an attached Service Role, and you have to configure your AWS boto3 profile locally, then export the profile name as an environment variable for the code to work locally. Refer to [this guide here](link-this-to-the-AWS-Guide) to see how to configure your IAM user profiles with its profile credentials via AWS CLI.
- `REGION` The region of your AWS services. See [list of AWS regions and the respective region codes](https://docs.aws.amazon.com/pdfs/global-infrastructure/latest/regions/regions-zones.pdf#aws-regions)
- `BUCKET`: The root path to your S3 bucket.
- `BINANCE_WEBSOCKET_SECRET_NAME`: <!--TO-DO: check in AWS Secrets Manager and write description -->

### Data processing metrics

```py
# Processing
MAX_BATCH_SIZE = 1000
MAX_BATCH_TIMEOUT = 10
```

- `MAX_BATCH_SIZE`: Size of data to microbatch into one JSONL file (in rows).
- `MAX_BATCH_TIMEOUT`: Amount of time (in seconds) before forcing a mircobatch to avoid long timeouts.

### DynamoDB metrices
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
- `signal`: Handle manual shutdown such as intercepting`Ctrl + C` signals gracefully.
- `asyncio`: Used in all asynchronous functions and procedures.
- `boto3`: Create boto3 sessions to allow user to call AWS services via configured IAM user.
- `binance`: Binance module to connect to the Binance websocket. Refer to this [websocket documentation](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams) by Binance.
