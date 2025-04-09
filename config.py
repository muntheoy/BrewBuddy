import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:1234root@localhost/lisa'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'your_jwt_secret_key'
    JWT_ACCESS_TOKEN_EXPIRES = 900  # 15 минут в секундах
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 дней в секундах
    SECRET_KEY = 'your_secret_key'