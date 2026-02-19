## Crypto Live Web (Next.js)

Next.js 14 dashboard that surfaces the latest mini‑ticker snapshots written by the ingestion pipeline to DynamoDB (and optionally S3 for historical curves).

### Quick start

1. `cd web`
2. `npm install`
3. Copy `.env.example` to `.env.local` and fill values:
   - `AWS_REGION` — same region as the pipeline (e.g. `ap-southeast-1`)
   - `DYNAMO_TABLE_NAME` — e.g. `crypto-live-miniticker`
   - `UI_STREAMS` — comma‑separated stream keys from Secrets Manager (`btcusdt@miniTicker,ethusdt@miniTicker,...`)
   - Standard AWS credentials are read from env (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) or the Vercel AWS role.
4. `npm run dev` and open `http://localhost:3000`.

### How data is read

- Each stream key (e.g. `btcusdt@miniTicker`) is a DynamoDB partition (`stream_type`). The API route queries the latest item per stream (Limit 1, descending) to avoid scans.
- Price rows are parsed via Zod (`PriceRowSchema`). Percent deltas are placeholders until historical windows are derived from S3/Glue (see below).

### Deploying to Vercel

- Node.js 18+ runtime; `runtime = 'nodejs'` is pinned in the API route for AWS SDK support.
- Set the same env vars in Vercel (`AWS_REGION`, `DYNAMO_TABLE_NAME`, `UI_STREAMS`, plus AWS creds or attach an IAM role via Vercel Integrations).

### Extending with S3 history

- The pipeline also writes gzip JSONL batches to S3. You can add another API route that reads the latest Parquet/JSONL to compute 1H/24H/7D deltas and sparkline charts.
- Keep queries bounded by prefix + timestamp to avoid full-bucket scans. Glue tables can help with Athena/Presto queries if desired.
