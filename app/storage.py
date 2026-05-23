import os
import boto3
from botocore.config import Config
from fastapi import UploadFile
import secrets
from dotenv import load_dotenv

load_dotenv()

R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_PUBLIC_CUSTOM_DOMAIN = os.getenv("R2_PUBLIC_CUSTOM_DOMAIN") 

s3_client = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.storage.supabase.co/storage/v1/s3", 
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(
        signature_version="s3v4",
        region_name="ap-southeast-1" 
    ),
)

def upload_profile_image(file: UploadFile) -> str:
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise ValueError("Invalid file extension format.")
        
    unique_filename = f"{secrets.token_hex(16)}{file_ext}"
    
    s3_client.upload_fileobj(
        file.file,
        R2_BUCKET_NAME,
        unique_filename,
        ExtraArgs={"ContentType": file.content_type}
    )
    
    return f"{R2_PUBLIC_CUSTOM_DOMAIN}/{unique_filename}"