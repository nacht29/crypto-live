import asyncio
import json
import signal
import boto3
from botocore.exceptions import ClientError
from typing import *

# retrieve secret from Secrets Manager
# get the stream symbol for each coin for miniTicker stream 
def get_secret(secret_name:str, region_name:str, profile_name:str) -> Dict:
	secret_name = secret_name
	region_name = region_name

	# create a Secrets Manager client
	try:
		session = boto3.session.Session(profile_name=profile_name)
		client = session.client(
			service_name='secretsmanager',
			region_name=region_name
		)
	except Exception as error:
		print(f"Failed to create boto3 client.\n\n{error}")
		raise

	# retrieve secret from secret ID
	try:
		get_secret_value_response = client.get_secret_value(SecretId=secret_name)
	except ClientError as error:
		print(f"Failed to retrieve secret.\n\n{error}") 
		raise

	secret = get_secret_value_response['SecretString']
	return json.loads(secret)

# make stream data more readable
def format_stream_data(stream_data:Dict):
	stream = stream_data['stream']
	data = stream_data['data']

	try:
		format_data = {
			'event_type': data['e'],
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
