import asyncio
import json
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from binance import AsyncClient, BinanceSocketManager

REGION = "ap-southeast-1"
PIPELINE_IAM_USER = "crypto-live-pipeline01"
BINANCE_WEBSOCKET_SECRET_NAME = "crypto-live.binance_ws"

def get_secret(secret_name:str, region_name:str, profile_name:str):
	secret_name = secret_name
	region_name = region_name

	# Create a Secrets Manager client
	session = boto3.session.Session(profile_name=profile_name)
	client = session.client(
		service_name='secretsmanager',
		region_name=region_name
	)

	try:
		get_secret_value_response = client.get_secret_value(
			SecretId=secret_name
		)
	except ClientError as error:
		print(f"Failed to retrieve secret.\n\n{error}") 
		raise

	secret = get_secret_value_response['SecretString']
	return secret

async def websocket():
	print(1)

async def load_s3():
	pass

def main():
	# retrieve secret as JSON str and load into dict
	ws_secret = get_secret(BINANCE_WEBSOCKET_SECRET_NAME, REGION, PIPELINE_IAM_USER)
	ws_urls = json.loads(ws_secret)
	
	for symbol in ws_urls.keys():
		print(symbol, ws_urls[symbol])
		asyncio.run(websocket())

if __name__ == '__main__':
	main()