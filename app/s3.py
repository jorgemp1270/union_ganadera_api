import boto3
import os

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Internal client — used for server-side operations (upload, delete).
# Uses the Docker-internal hostname (e.g. http://localstack:4566).
s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
)

# Public client — used ONLY for generating presigned URLs that external clients
# (mobile app, browser) will access directly.
# Set S3_PUBLIC_URL to the externally-reachable address of LocalStack/S3,
# e.g. http://192.168.1.100:4566 or https://s3.amazonaws.com
# Falls back to S3_ENDPOINT_URL if S3_PUBLIC_URL is not set.
_public_endpoint = os.getenv("S3_PUBLIC_URL") or os.getenv("S3_ENDPOINT_URL")

s3_public_client = boto3.client(
    "s3",
    endpoint_url=_public_endpoint,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
)
