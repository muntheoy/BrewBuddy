import boto3
from flask import current_app
import uuid

def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )

def upload_file_to_s3(file, folder="products"):
    """
    Загружает файл в S3 и возвращает URL
    """
    try:
        s3_client = get_s3_client()
        
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{folder}/{uuid.uuid4()}.{file_extension}"
        
        # Загружаем файл
        s3_client.upload_fileobj(
            file,
            current_app.config['S3_BUCKET'],
            unique_filename,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': file.content_type
            }
        )

        file_url = f"{current_app.config['S3_BUCKET_URL']}/{unique_filename}"
        return file_url
        
    except Exception as e:
        current_app.logger.error(f"Error uploading file to S3: {str(e)}")
        raise 