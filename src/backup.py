import os
import asyncio
import tempfile

from pathlib import Path
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
			# create a temporaty file in "wb" mode to write bytes into the file
			with tempfile.NamedTemporaryFile("wb", delete=False, dir=output_dir) as tmp_file:
				# write string data as bytes row y row
				for row in batch_data:
					# turn string data to UTF-8 encoded bytes + a new line byte
					tmp_file.write(json.dumps(row, separators=(",", ":")).encode("utf-8"))
					tmp_file.write(b"\n")

				# replace bin file with physical JSON
				tmp_filepath = Path(tmp_file.name)
				outfile_path = Path(f"{output_dir}/{outfile_name}")
				os.replace(tmp_filepath, outfile_path)

		finally:
			batch_queue.task_done()
