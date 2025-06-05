from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import Config
import os
from .extensions import db, jwt
from .routes.auth import auth_bp
from .routes.products import products_bp
from .routes.orders import orders_bp
from .routes.admin import admin_bp
from .routes.payment_routes import payment_bp, init_payment_service

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)

    init_payment_service(app)

    # Создаем директорию для загрузок, если она не существует
    upload_folder = os.path.join(app.static_folder, 'uploads', 'products')
    os.makedirs(upload_folder, exist_ok=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp, url_prefix='/payments')

    return app