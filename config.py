import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///brewbuddy.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT   
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 дней в секундах

    # YooMoney
    YOOMONEY_API_KEY = os.environ.get('YOOMONEY_API_KEY') or 'test_RmuhggbVDh5ExF3v2TXflw94s_cP4lHXtRPfX1fjJPE'
    YOOMONEY_SHOP_ID = os.environ.get('YOOMONEY_SHOP_ID') or '1088812'  # ID магазина в ЮKassa
    YOOMONEY_RETURN_URL = os.environ.get('YOOMONEY_RETURN_URL') or 'http://localhost:5000/api/payments/verify'
    YOOMONEY_TEST_MODE = True  # Режим тестирования

    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET = os.getenv('S3_BUCKET')
    S3_BUCKET_URL = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com"