import boto3
import os
from botocore.config import Config

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "documentos")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localstack:4566")
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL", "http://localhost:4566")

# Internal client — used for server-side operations (upload, delete).
# Uses the Docker-internal hostname (e.g. http://localstack:4566).
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}  # Path style for LocalStack compatibility
    )
)

# Public client — used ONLY for generating presigned URLs that external clients
# (mobile app, browser) will access directly.
# Set S3_PUBLIC_URL to the externally-reachable address of LocalStack/S3,
# e.g. http://localhost:4566 or https://s3.amazonaws.com
s3_public_client = boto3.client(
    "s3",
    endpoint_url=S3_PUBLIC_URL,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}  # Path style for LocalStack compatibility
    )
)
