import os
import asyncio
import json
import tempfile
import signal
from binance import AsyncClient, BinanceSocketManager
from pathlib import Path
from typing import *
from datetime import datetime
from typing import *
from utils import *

# AWS constants
REGION = "ap-southeast-1"
PIPELINE_IAM_USER = "crypto-live-pipeline01"
BINANCE_WEBSOCKET_SECRET_NAME = "crypto-live.binance_ws"

# Processing
MAX_BATCH_SIZE = 5 # change to 5000 for prod
MAX_BATCH_TIMEOUT = 2 # wait 2 seconds for input or force flush (batch)
BATCH_JSON_FILES = "/mnt/c/Users/Asus/Desktop/crypto-live/batch_json"

async def websocket_ingest(client:AsyncClient, streams:List, raw_queue:asyncio.Queue):
	# create Binance Socket Manager client
	bm = BinanceSocketManager(client)

	async with bm.multiplex_socket(streams) as socket:
		while True:
			stream_data = await socket.recv()
			formatted_data = format_stream_data(stream_data)
			print(formatted_data)
			await raw_queue.put(formatted_data)

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
			last_flush = loop.time
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
		except Exception as error:
			await flush()

async def write_to_file(batch_queue:asyncio.Queue, output_dir:str, outfile_name_format:str):
	# ensure output directory exists
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	
	while True:
		# retrieve batch data
		batch_data = await batch_queue.get()

		# filename + timestamp
		timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
		outfile_name = f"{outfile_name_format}-{timestamp}.jsonl"
		
		
		try:
			# writing
			with tempfile.NamedTemporaryFile("wb", delete=False, dir=output_dir) as tmp_file:
				# create temp file to write binary data to
				for row in batch_data:
					tmp_file.write(json.dumps(row, separators=(",", ":")).encode("utf-8"))
					tmp_file.write(b"\n")
				
				# replace bin file with physical JSON
				tmp_filepath = Path(tmp_file.name)
				outfile_path = Path(f"{output_dir}/{outfile_name}")
				os.replace(tmp_filepath, outfile_path)

		finally:
			batch_queue.task_done()

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
		batch = asyncio.create_task(batch_data(raw_queue, batch_queue, max_batch=MAX_BATCH_SIZE, max_timeout=MAX_BATCH_TIMEOUT))
		write = asyncio.create_task(write_to_file(batch_queue, output_dir=BATCH_JSON_FILES, outfile_name_format="sample"))
		
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