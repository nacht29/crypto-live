DROP TABLE crypto_live_db.test;

CREATE EXTERNAL TABLE crypto_live_db.test (
	event_type STRING,
	symbol STRING,
	close_price STRING,
	open_price STRING,
	high_price STRING,
	low_price STRING,
	total_traded_volume STRING,
	total_traded_base_asset_volume STRING
)
PARTITIONED BY (stream_type STRING)
STORED AS parquet
LOCATION 's3://crypto-live-bucket/parquet/';

MSCK REPAIR TABLE crypto_live_db.test;
-- SHOW PARTITIONS crypto_live_db.test;

SELECT DISTINCT stream_type FROM crypto_live_db.test;

SELECT *
FROM crypto_live_db.test
WHERE stream_type = 'ethusdt@miniTicker'
LIMIT 10;

