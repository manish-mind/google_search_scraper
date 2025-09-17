import boto3
import os
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

load_dotenv()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

BUCKET = os.getenv("AWS_S3_BUCKET_NAME")

executor = ThreadPoolExecutor()


async def upload_to_s3(file_bytes: bytes, s3_key: str):
    loop = asyncio.get_event_loop()
    try:
        func = partial(s3_client.put_object, Bucket=BUCKET, Key=s3_key, Body=file_bytes)
        await loop.run_in_executor(executor, func)
        return f"s3://{BUCKET}/{s3_key}"
    except Exception as e:
        raise RuntimeError(f"Upload failed for {s3_key}: {e}")