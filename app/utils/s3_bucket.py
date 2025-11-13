# app/utils/s3_bucket.py
import os
import uuid
import base64
import mimetypes
from fastapi import HTTPException, UploadFile
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# 환경변수에서 S3 설정 가져오기
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")

# S3 클라이언트 초기화
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)


def upload_image_to_s3(file: "UploadFile | str", folder: str = "uploads") -> str:
    """
    S3에 이미지 업로드 후, public URL을 반환합니다.
    - file: UploadFile 객체 (form-data) 또는 base64 문자열
    - folder: S3 저장 폴더 (prefix)
    - 반환: S3 접근 가능한 URL (DB에 저장할 image_url)
    """
    try:
        # UploadFile 객체인 경우
        if hasattr(file, "file"):
            file_bytes = file.file.read()
            content_type = file.content_type
        else: # base64 문자열인 경우
            header, encoded = file.split(",", 1) if "," in file else ("", file)
            file_bytes = base64.b64decode(encoded)
            content_type = header.split(";")[0].split(":")[-1] if header else "image/jpeg"

        # 확장자 추정
        extension = mimetypes.guess_extension(content_type) or ".jpg"

        # S3 저장 파일명
        unique_filename = f"{uuid.uuid4()}{extension}"
        key = f"{folder}/{unique_filename}"

        # 업로드
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
            ACL="public-read",
        )

        # S3 URL 반환 (DB에 저장할 image_url)
        return f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"

    except (NoCredentialsError, ClientError, Exception) as e:
        raise HTTPException(status_code=500, detail=f"S3 업로드 실패: {str(e)}")


def get_image_url(key: str) -> str:
    """
    DB에 저장된 image_url을 기반으로 최종 접근 가능한 URL 반환.
    - key: S3 key 혹은 파일명 (이미 URL이면 그대로 반환 가능)
    """
    if key.startswith("http"):
        return key
    return f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
