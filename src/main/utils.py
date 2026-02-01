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
def get_secret(session, secret_name:str, region_name:str) -> dict:
	secret_name = secret_name
	region_name = region_name

	# create a Secrets Manager client
	try:
		client = session.client(service_name='secretsmanager', region_name=region_name)
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

# ===========================
# = Raw data transformation =
# ===========================

# process numeric and datetime values
def process_dt_numeric(object:dict, dt_type:str='dt', numeric_str:str='num') -> dict:
	if dt_type not in ['str', 'dt'] or numeric_str not in ['str', 'num']:
		raise ValueError("Invalid dt_type. Only accept 'dt' for type <datetime> and 'str' for type <str>")
	if numeric_str not in ['str', 'num']:
		raise ValueError("Invalid numeric_str. Only accept 'num' for type <int> or type <Decimal> and 'str' for type <str>")

	out_object = {}

	for key, value in object.items():
		if key == 'event_time':
			out_object[key] = value
			# convert epoch time (ms) to date time: e.g. 1700000000123 to 2023-11-14T22-13-20.123000 
			iso_timestamp = datetime.utcfromtimestamp(value / 1000)
			if dt_type == 'str':
				out_object['iso_timestamp'] = iso_timestamp.strftime("%Y-%m-%dT%H-%M-%S.%fZ")
			else:
				out_object['iso_timestamp'] = iso_timestamp
		elif numeric_str == 'num' and isinstance(object[key], str) and value.replace('.', '', 1).isdigit():
			out_object[key] = Decimal(value)
			continue
		else:
			out_object[key] = value

	return out_object

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
