import signal
import asyncio
import boto3
from binance import AsyncClient, BinanceSocketManager
from typing import *
from datetime import datetime
from time import time
from typing import *
from utils import *

# AWS constants
REGION = "ap-southeast-1"
PIPELINE_IAM_USER = "crypto-live-pipeline01"
BINANCE_WEBSOCKET_SECRET_NAME = "crypto-live.binance_ws"
BUCKET = "crypto-live-bucket"
BATCH_JSONL_BUCKET_DIR = "batch_jsonl"

# Processing
MAX_BATCH_SIZE = 1000 # change to 5000 for prod
MAX_BATCH_TIMEOUT = 10 # wait 2 seconds for input or force flush (batch)

# DynamoDB
RETENTION_TTL_DAYS = 1
TABLE_NAME = "crypto-live-miniticker"

# create boto3 session
def create_boto3_session(profile, region) -> boto3.session:
	try:
		session = boto3.session.Session(profile_name=profile, region_name=region)
	except Exception as error:
		print(f"Failed to create boto3 session.\n\n{error}")
		raise

	return session

async def websocket_ingest(client:AsyncClient, streams:List, dynamo_raw_queue:asyncio.Queue, s3_raw_queue:asyncio.Queue):
	# create Binance Socket Manager client
	bm = BinanceSocketManager(client)

	async with bm.multiplex_socket(streams) as socket:
		while True:
			stream_data = await socket.recv()
			formatted_data = format_stream_data(stream_data)
			# print(formatted_data)
			await dynamo_raw_queue.put(formatted_data)
			await s3_raw_queue.put(process_dt_numeric(formatted_data, dt_type='str', numeric_str='str'))

async def batch_data(raw_queue:asyncio.Queue, batch_queue:asyncio.Queue, max_batch:int, max_timeout:int):
	buffer = []
	loop = asyncio.get_running_loop()
	last_flush = loop.time()

	# flush and reset buffer
	# reset last_flush
	async def flush():
		nonlocal buffer, last_flush
		# reset flush time if buffer is empty
		if not buffer:
			last_flush = loop.time()
			return
		# batch data
		await batch_queue.put(buffer)
		# reset flush state
		buffer = []
		last_flush = loop.time()

	while True:
		# calculate elapsed time and remaining flush window
		# when elapsed > max window, flush_window = 0 aka 0 seconds until next flush (timeout)
		elapsed = loop.time() - last_flush
		flush_window = max(0.0, max_timeout - elapsed)

		try:
			# wait for message in queue within remaining flush window
			data = await asyncio.wait_for(raw_queue.get(), timeout=flush_window)
			# add data to buffer
			buffer.append(data)

			# when max batch size is reached, flush the data (batching)
			if len(buffer) >= max_batch or flush_window <= 0:
				await flush()
		
		# no message arrived within flush window
		except asyncio.TimeoutError as error:
			await flush()

async def write_to_dynamodb(session, raw_queue:asyncio.Queue, concurrency:int=20, ttl_days:int | None = None):
	dynamo = session.resource(service_name="dynamodb")
	table = dynamo.Table(TABLE_NAME)
	sem = asyncio.Semaphore(concurrency)

	async def write():
		while True:
			raw = await raw_queue.get()
			try:
				formatted_data = process_dt_numeric(raw, dt_type='str', numeric_str='num')
				expression = [
					"event_type = :E",
					"event_time = :e",
					# "iso_timestamp = :i", -- partition key is excluded
					# "stream_type = :S", -- sorting key is excluded
					"symbol = :s",
					"close_price = :c",
					"open_price = :o",
					"high_price = :h",
					"low_price = :l",
					"total_traded_volume = :v",
					"total_traded_base_asset_volume = :q"
				]
				values = {
					':E': formatted_data['event_type'],
					':e': formatted_data['event_time'],
					':s': formatted_data['symbol'],
					':c': formatted_data['close_price'],
					':o': formatted_data['open_price'],
					':h': formatted_data['high_price'],
					':l': formatted_data['low_price'],
					':v': formatted_data['total_traded_volume'],
					':q': formatted_data['total_traded_base_asset_volume']
				}

				if ttl_days is not None:
					values[':ttl_days'] = int(time()) + ttl_days*24*360
					expression.append("ttl_days = :ttl_days")

				update_expression = "SET " + ", ".join(expression)

				async with sem:
					await asyncio.to_thread(
						table.update_item,
						Key = {
							'stream_type': formatted_data['stream_type'],
							'iso_timestamp': formatted_data['iso_timestamp']
						},
						UpdateExpression=update_expression,
						ExpressionAttributeValues=values
					)

					print(f"{datetime.now()} Wrote 1 row to DynamodDB.")

			finally:
				raw_queue.task_done()
	
	# create parallet (concurrent) threads to write to DynamoDB
	# global cap is set = concurrent so that no huge spikes occur
	tasks = [asyncio.create_task(write()) for _ in range(concurrency)]
	await asyncio.gather(*tasks)

async def write_to_s3(session, batch_queue:asyncio.Queue, bucket:str, bucket_dir:str, filename:str, gzip:bool=True, sse:str | None  = None, sse_kms_key_id:str | None = None):
	
	s3_client = session.client(service_name="s3")
	
	while True:
		# retrieve data from queue
		batch_data = await batch_queue.get()

		try:
			# write batch data as bytes to BytesIO buffer
			# the buffer is the file body to be uploaded
			file_body = write_jsonl_bytes(batch_data)

			# zip the file
			if gzip:
				file_body = gzip_file(file_body)

			datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

			#  file config
			timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
			file_key = f"{bucket_dir}/{filename.removesuffix(".jsonl")}-{timestamp}.jsonl" # file name
			
			extra = {}
			if gzip:
				extra["ContentEncoding"] = "gzip"
				extra["ContentType"] = "application/json"
			if sse:
				extra["ServerSideEncryption"] = sse
			if sse_kms_key_id:
				extra["SSEKMSKeyId"] = sse_kms_key_id

			# offload writing to S3 to another thread as it blocks the thread due to HTTP request
			await asyncio.to_thread(
				s3_client.put_object,
				Bucket=bucket,
				Key=file_key,
				Body=file_body,
				**extra,
			)

			# logging
			print(f"{datetime.now()} Uploaded {filename.removesuffix(".jsonl")}-{timestamp}.jsonl")

		finally:
			batch_queue.task_done()

async def main(load_s3:bool=True, load_dynamod:bool=True):
	# create boto3_session
	session = create_boto3_session(profile=PIPELINE_IAM_USER, region=REGION)

	# retrieve secret as JSON str and load into dict
	secret = get_secret(session, BINANCE_WEBSOCKET_SECRET_NAME, REGION, PIPELINE_IAM_USER)
	streams = secret['streams']

	# create async client
	client = await AsyncClient.create(testnet=True)

	# create async queues
	dynamo_raw_queue = asyncio.Queue(maxsize=10000)
	s3_raw_queue = asyncio.Queue(maxsize=10000)
	batch_queue = asyncio.Queue(maxsize=1000)

	# orchestration
	try:
		print(f"{datetime.now()} Init tasks")
	
		# create tasks
		ingest = asyncio.create_task(websocket_ingest(client=client, streams=streams, dynamo_raw_queue=dynamo_raw_queue, s3_raw_queue=s3_raw_queue))
		batch = asyncio.create_task(batch_data(s3_raw_queue, batch_queue, max_batch=MAX_BATCH_SIZE, max_timeout=MAX_BATCH_TIMEOUT))
		tasks  = [ingest, batch]

		if load_s3:
			write_s3 = asyncio.create_task(write_to_s3(session, batch_queue, bucket=BUCKET, bucket_dir=BATCH_JSONL_BUCKET_DIR, filename="miniticker", gzip=True))
			tasks.append(write_s3)
		if load_dynamod:
			write_dynamod = asyncio.create_task(write_to_dynamodb(session, dynamo_raw_queue, ttl_days=RETENTION_TTL_DAYS))
			tasks.append(write_dynamod)

		# handle shutdown for CTRL+C or when container ends
		# when signal is intercepted, set stop = True and unblock await stop.wait()
		# this allows the shutdown logic tp exeute
		stop = asyncio.Event()
		loop = asyncio.get_running_loop()
		for sig in (signal.SIGINT, signal.SIGTERM):
			loop.add_signal_handler(sig, stop.set)
		await stop.wait()

		# shutdown logic
		for task in tasks:
			task.cancel()

		print(f"{datetime.now()} Exec tasks")

		# run tasks concurrently
		await asyncio.gather(*tasks)

	finally:
		await client.close_connection()

if __name__ == '__main__':
	asyncio.run(main(load_s3=True, load_dynamod=True))
