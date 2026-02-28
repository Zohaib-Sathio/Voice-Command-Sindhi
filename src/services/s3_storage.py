"""
S3 storage service for audio files.
Handles uploading and managing audio files in AWS S3.
"""
import boto3
import os
from botocore.exceptions import ClientError
from typing import Optional
from dotenv import load_dotenv

load_dotenv(override=True)

# S3 Configuration from environment variables
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize S3 client (None if credentials not provided)
s3_client = None
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    s3_client = boto3.client(
        's3',
        region_name=S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
elif S3_BUCKET_NAME:
    # Fallback to IAM role credentials (for EC2/ECS/Lambda)
    s3_client = boto3.client('s3', region_name=S3_REGION)


def upload_audio_file(file_content: bytes, file_key: str, content_type: str = "audio/webm") -> Optional[str]:
    """
    Upload audio file to S3 bucket.
    
    Args:
        file_content: File content as bytes
        file_key: S3 object key (path in bucket)
        content_type: MIME type of the file
        
    Returns:
        S3 object URL if successful, None otherwise
    """
    print("S3 Storage: Uploading audio file to S3...")
    if not s3_client or not S3_BUCKET_NAME:
        print("⚠️ S3 not configured - skipping upload")
        return None
    
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=file_content,
            ContentType=content_type
        )
        
        # Generate S3 URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{file_key}"
        print(f"✅ Uploaded {file_key} to S3")
        return s3_url
        
    except ClientError as e:
        print(f"❌ Failed to upload to S3: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error uploading to S3: {e}")
        return None


def delete_audio_file(file_key: str) -> bool:
    """
    Delete audio file from S3 bucket.
    
    Args:
        file_key: S3 object key to delete
        
    Returns:
        True if successful, False otherwise
    """
    if not s3_client or not S3_BUCKET_NAME:
        return False
    
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=file_key)
        print(f"✅ Deleted {file_key} from S3")
        return True
    except Exception as e:
        print(f"❌ Failed to delete from S3: {e}")
        return False

