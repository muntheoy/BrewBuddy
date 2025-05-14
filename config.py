import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OAuth
    YANDEX_CLIENT_ID = "277c63df2b334d18a6e995db14a5f741"
    YANDEX_CLIENT_SECRET = "40453d1909504eb1a963d01b819a0d42"
    
    # JWT 
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 дней в секундах

    # YooMoney
    YOOMONEY_API_KEY = os.environ.get('YOOMONEY_API_KEY') or 'test_u-XrvF5sJYZ-p3dkqSKpX3niLciecW2B0KQkmg6ioPU'
    YOOMONEY_SHOP_ID = os.environ.get('YOOMONEY_SHOP_ID') or '1086341'  # ID магазина в ЮKassa
    YOOMONEY_RETURN_URL = os.environ.get('YOOMONEY_RETURN_URL') or 'http://localhost:5000/api/payments/verify'
    YOOMONEY_TEST_MODE = True  # Режим тестирования