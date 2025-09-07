# crypto-live
Data pipeline and visualisation for popular cryptocurrency exchange rates

```mermaid
flowchart LR
  subgraph AWS[ap-southeast-1 AWS Account]
    direction LR
    A[Developer<br/>IAM User/Role]
    subgraph VPC[VPC (private subnets)]
      ECS[ECS Service<br/>Fargate Spot Task<br/>Python asyncio]
    end
    SM[Secrets Manager<br/>Binance creds]
    S3[(Amazon S3<br/>raw JSON → parquet)]
    GLUE[Glue Crawler/Jobs<br/>Data Catalog]
    ATH[Athena<br/>SQL on S3]
    CW[CloudWatch Logs/Metrics<br/>Alarms→SNS]
    BZ[(Binance miniTicker WS)]
  end

  A--deploy/ops-->ECS
  SM--read secret-->ECS
  BZ--wss feed-->ECS
  ECS--micro-batched JSON-->S3
  S3--lifecycle-->S3
  GLUE--crawl schema-->S3
  GLUE--write Parquet-->S3
  ATH--queries partitioned parquet-->S3
  ECS--app logs/metrics-->CW
  CW--alerts-->A

```