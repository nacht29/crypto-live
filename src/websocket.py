import asyncio
import signal
from botocore.exceptions import ClientError
from typing import *
from binance import AsyncClient, BinanceSocketManager
from typing import *
from utils import *

# AWS constants
REGION = "ap-southeast-1"
PIPELINE_IAM_USER = "crypto-live-pipeline01"
BINANCE_WEBSOCKET_SECRET_NAME = "crypto-live.binance_ws"

# Processing
BATCH_SIZE = 100 # change to 5000 for prod
BATCH_TIMEOUT = 2 # wait 2 seconds for input or force flush (batch)

async def websocket_ingest(client:AsyncClient, streams:List, raw_queue:asyncio.Queue):
	# create Binance Socket Manager client
	bm = BinanceSocketManager(client)

	async with bm.multiplex_socket(streams) as socket:
		while True:
			stream_data = await socket.recv()
			formatted_data = format_stream_data(stream_data)
			print(formatted_data)
			await raw_queue.put(formatted_data)

async def batch_data():
	pass

async def write_to_file():
	pass

async def main():
	# retrieve secret as JSON str and load into dict
	secret = get_secret(BINANCE_WEBSOCKET_SECRET_NAME, REGION, PIPELINE_IAM_USER)
	streams = secret['streams']

	# create async client
	client = await AsyncClient.create()

	# create async queues
	raw_queue = asyncio.Queue(maxsize=10000)
	batch_queue = asyncio.Queue(maxsize=1000)

	# orchestration
	try:
		# create tasks
		ingest = asyncio.create_task(websocket_ingest(client=client, streams=streams, raw_queue=raw_queue))
		batch = asyncio.create_task(batch_data())
		write = asyncio.create_task(write_to_file())
		
		tasks  = [ingest, batch, write]

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

		# run tasks concurrently
		await asyncio.gather(ingest, batch, write)

	finally:
		await client.close_connection()

if __name__ == '__main__':
	asyncio.run(main())