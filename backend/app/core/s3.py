import uuid
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings


def _get_s3_client():
    kwargs = {"region_name": settings.AWS_REGION}
    if settings.AWS_ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.client("s3", **kwargs)


def upload_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Upload a file to S3 and return the S3 key."""
    s3 = _get_s3_client()
    key = f"uploads/{uuid.uuid4()}/{filename}"

    s3.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return key


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for a stored file."""
    s3 = _get_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires_in,
    )


def file_exists(key: str) -> bool:
    """Check if a file exists in S3."""
    s3 = _get_s3_client()
    try:
        s3.head_object(Bucket=settings.S3_BUCKET, Key=key)
        return True
    except ClientError:
        return False
