import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
job.commit()

# Load JSONL from S3 (raw)
datasource = glueContext.create_dynamic_frame.from_catalog(
	database="crypto_live_db",
	table_name="raw_batch_jsonl"
)

# Convert to Parquet (with partitioning by dt/hour)
datasink = glueContext.write_dynamic_frame.from_options(
	frame=datasource,
	connection_type="s3",
	connection_options={
		"path": "s3://crypto-live-bucket/parquet/",
		"partitionKeys": ["stream", "symbol"]
	},
	format="parquet",
	format_options={"compression": "snappy"}
)

job.commit()
