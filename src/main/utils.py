import io
import json
import gzip
from datetime import datetime
from decimal import Decimal
from typing import *

# ===================
# = Secrets Manager =
# ===================

# retrieve secret from Secrets Manager
# get the stream symbol for each coin for miniTicker stream 
def get_secret(session, secret_name:str, region_name:str, profile_name:str) -> dict:
	secret_name = secret_name
	region_name = region_name

	# create a Secrets Manager client
	try:
		client = session.client(service_name='secretsmanager',region_name=region_name)
	except Exception as error:
		print(f"Failed to create boto3 session for Secrets Manager.\n\n{error}")
		raise

	# retrieve secret from secret ID
	try:
		get_secret_value_response = client.get_secret_value(SecretId=secret_name)
	except Exception as error:
		print(f"Failed to retrieve secret.\n\n{error}") 
		raise

	secret = get_secret_value_response['SecretString']
	return json.loads(secret)

# ===============
# = S3 functions=
# ===============
def write_jsonl_bytes(batch_data:list[dict]) -> bytes:
	jsonl_buffer = io.BytesIO()

	for row in batch_data:
		jsonl_buffer.write(json.dumps(row, separators=[",", ":"]).encode("utf-8"))
		jsonl_buffer.write(b"\n")

	return jsonl_buffer.getvalue()

def gzip_file(data:bytes) -> bytes:
	gzip_buffer = io.BytesIO()

	with gzip.GzipFile(fileobj=gzip_buffer, mode='wb') as open_buffer:
		open_buffer.write(data)

	return gzip_buffer.getvalue()

# ==================
# = DynamoDB Utils =
# ==================

# converts numerical string to decimal from websocket data
def format_dynamo_data(object:dict) -> dict:
	formatted_object = {}

	for key, value in object.items():
		# replace('.', '', 1) -> only replaces one decimal point '.'
		# valid decimals only have one '.'
		if key == 'event_time':
			formatted_object[key] = value
			# divide by 1000 to convert UNIX ms to seconds
			# convert UNIX seconds to timestamp
			iso_timestamp = datetime.utcfromtimestamp(value / 1000)
			# convert datetime to string (DynamoDB cannot accept datetime object)
			formatted_object['iso_timestamp'] = iso_timestamp.strftime("%Y-%m-%dT%H-%M-%s.%fZ")
		elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
			formatted_object[key] = Decimal(value)
		else:
			formatted_object[key] = value

	return formatted_object

# =====================
# = Utility functions =
# =====================

# make stream data more readable
def format_stream_data(stream_data:dict) -> dict:
	stream_type = stream_data.get('stream_type') or stream_data.get('stream')
	if stream_type is None:
		raise KeyError('stream_type')
	data = stream_data['data']

	try:
		format_data = {
			'event_type': data['e'],
			'event_time': data['E'],
			'stream_type': stream_type,
			'symbol': data['s'],
			'close_price': data['c'],
			'open_price': data['o'],
			'high_price': data['h'],
			'low_price': data['l'],
			'total_traded_volume': data['v'],
			'total_traded_base_asset_volume': data['q']
		}
	except Exception as error:
		print(f"Failed to format stream data.\n\n{error}")
		raise
	
	return format_data

