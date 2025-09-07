# pip install diagrams
# Install Graphviz and ensure `dot` is on PATH

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import SNS
from diagrams.aws.security import IAM
from diagrams.aws.network import VPC
from diagrams.aws.general import General
from diagrams.onprem.client import User
from diagrams.onprem.network import Internet

with Diagram(
    "Crypto Prices Pipeline (AWS)",
    filename="aws2",
    show=False,
    direction="LR",  # left -> right
    graph_attr={"splines": "ortho", "nodesep": "0.7", "ranksep": "1.0"},
    edge_attr={"fontsize": "10"},
):
    # External actors (kept outside the AWS Account)
    dev = User("Developer\nIAM User/Role")
    binance = Internet("Binance miniTicker WS\n(wss)")

    with Cluster("ap-southeast-1 AWS Account"):
        # ----- Column 1: Security & Cost -----
        with Cluster("Security & Cost"):
            iam = IAM("IAM\nRoles/Policies")
            secrets = General("Secrets Manager\n(API credentials)")
            budgets = General("AWS Budgets\n(cost alerts)")

        # ----- Column 2: VPC / Compute -----
        with Cluster("VPC (private subnets)"):
            vpc = VPC("VPC")
            ecs = ECS("ECS Service\nFargate (Spot)\nPython container (asyncio)")
            # keep label node and ECS on same row
            vpc - Edge(style="invis") - ecs

        # ----- Column 3: Data Lake & Metadata -----
        with Cluster("Data Lake & Metadata"):
            s3 = S3("Amazon S3\nRaw JSON → Parquet")
            glue = General("AWS Glue\nCrawler + Jobs")
            athena = General("Amazon Athena\nQuery Parquet on S3")
            # gentle horizontal ordering within the cluster
            s3 - Edge(style="invis") - glue
            glue - Edge(style="invis") - athena

        # ----- Column 4: Observability -----
        with Cluster("Observability"):
            cw = Cloudwatch("CloudWatch\nLogs/Metrics\nAlarms → SNS")
            sns = SNS("Amazon SNS")
            cw - Edge(style="invis") - sns

        # ===== Invisible spine to force left->right column order =====
        # (This avoids criss-crossing and angled edges by guiding layout.)
        iam - Edge(style="invis") - ecs
        ecs - Edge(style="invis") - s3
        s3 - Edge(style="invis") - glue
        glue - Edge(style="invis") - athena
        athena - Edge(style="invis") - cw
        cw - Edge(style="invis") - sns

        # ===== Real edges (runtime flow & relations) =====
        # Access / IAM
        iam >> Edge(label="assume / grant") >> dev
        iam >> Edge(label="task role") >> ecs
        iam >> Edge(label="access policy") >> secrets
        dev >> Edge(label="deploy / ops") >> ecs

        # Ingestion
        binance >> Edge(label="wss feed") >> ecs
        secrets >> Edge(label="read creds") >> ecs

        # Storage & processing
        ecs >> Edge(label="micro-batches (JSON)") >> s3
        glue >> Edge(label="compaction / write Parquet") >> s3
        s3 >> Edge(label="crawl partitions / schema") >> glue

        # Query
        athena >> Edge(label="query on demand") >> s3

        # Observability & alerts
        ecs >> Edge(label="logs / metrics") >> cw
        cw  >> Edge(label="notify") >> sns
        sns >> Edge(label="alerts") >> dev

        # Cost guardrails
        budgets >> Edge(label="budget thresholds") >> dev
