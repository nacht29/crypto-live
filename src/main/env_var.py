import os
from utils import *

# =====================
# = Pipeline integriy =
# =====================

def aws_write_params() -> Tuple[int, int]:
	s3_write = os.getenv("S3_WRITE", 1)
	dynamo_write = os.getenv("DYNAMO_WRITE", 1)

	try:
		s3_write = int(s3_write)
		if not 0 <= s3_write <= 1:
			raise ValueError("S3_WRTIE env must be 0 or 1.")
	except ValueError:
		raise ValueError("S3_WRTIE env must be 0 or 1.")
	try:
		dynamo_write = int(dynamo_write)
		if not 0 <= dynamo_write <= 1:
			raise ValueError("DYNAMO_WRITE env must be 0 or 1.")
	except ValueError:
		raise ValueError("DYNAMO_WRITE env must be 0 or 1.")

	return s3_write, dynamo_write

# =================
# = ENV Variables =
# =================

# AWS boto3 config
PIPELINE_IAM_USER = os.getenv("PIPELINE_IAM_USER", "") # boto3 profile
REGION = os.getenv("REGION", "ap-southeast-1") # AWS region

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

# AWS services
S3_BUCKET = os.getenv("S3_BUCKET", "crypto-live-bucket") # S3 bucket
S3_JSONL_DIR_PATH = os.getenv("S3_JSONL_DIR_PATH", "batch_jsonl") # S3 bucket directory path to store raw JSONL
BINANCE_WEBSOCKET_SECRET = os.getenv("BINANCE_WEBSOCKET_SECRET", "crypto-live.binance_ws") # Secrets Manager - websocket url
DYNAMO_TABLE_NAME = os.getenv("DYNAMO_TABLE_NAME", "crypto-live-miniticker") # DynamoDB table name
try:
	RETENTION_TTL_DAYS = int(os.getenv("RETENTION_TTL_DAYS", 1)) # Days to retent data in DynamoDB table
except ValueError:
	print("Invalid TTL")
	raise(ValueError)

# Pipeline toggle
S3_WRITE, DYNAMO_WRITE = aws_write_params()

# Async Client
TESTNET = bool(os.getenv("TESTNET", True))

# AWS boto3 config
PIPELINE_IAM_USER = os.getenv("PIPELINE_IAM_USER", "") # boto3 profile
REGION = os.getenv("REGION", "ap-southeast-1") # AWS region

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

# AWS services
S3_BUCKET = os.getenv("S3_BUCKET", "crypto-live-bucket") # S3 bucket
S3_JSONL_DIR_PATH = os.getenv("S3_JSONL_DIR_PATH", "batch_jsonl") # S3 bucket directory path to store raw JSONL
BINANCE_WEBSOCKET_SECRET = os.getenv("BINANCE_WEBSOCKET_SECRET", "crypto-live.binance_ws") # Secrets Manager - websocket url
DYNAMO_TABLE_NAME = os.getenv("DYNAMO_TABLE_NAME", "crypto-live-miniticker") # DynamoDB table name
try:
	RETENTION_TTL_DAYS = int(os.getenv("RETENTION_TTL_DAYS", 1)) # Days to retent data in DynamoDB table
except ValueError:
	print("Invalid TTL")
	raise(ValueError)

# Pipeline toggle
S3_WRITE, DYNAMO_WRITE = aws_write_params()

# Async Client
TESTNET = bool(os.getenv("TESTNET", True))

# ===========
# = Logging =
# ===========

def print_env_var():
	env_var = {
		"PIPELINE_IAM_USER": PIPELINE_IAM_USER,
		"REGION": REGION,
		"MAX_BATCH_SIZE": MAX_BATCH_SIZE,
		"MAX_BATCH_TIMEOUT": MAX_BATCH_TIMEOUT,
		"S3_BUCKET": S3_BUCKET,
		"S3_JSONL_DIR_PATH": S3_JSONL_DIR_PATH,
		"BINANCE_WEBSOCKET_SECRET": BINANCE_WEBSOCKET_SECRET,
		"DYNAMO_TABLE_NAME": DYNAMO_TABLE_NAME,
		"RETENTION_TTL_DAYS": RETENTION_TTL_DAYS,
		"S3_WRITE": S3_WRITE,
		"DYNAMO_WRITE": DYNAMO_WRITE,
		"TESTNET": TESTNET
	}
	
	key_width = max(len(key) for key in env_var)
	value_width = max(len(str(value)) for value in env_var.values())

	for key, value in env_var.items():
		# format: key (tab align) = value (tab align) data_type
		print(f"{key:<{key_width}} =  {value:<{value_width}}  {type(value)}")
