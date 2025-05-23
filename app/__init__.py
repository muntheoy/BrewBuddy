from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from .extensions import db, jwt
from .routes.auth import auth_bp
from .routes.products import products_bp
from .routes.orders import orders_bp
from .routes.admin import admin_bp
from .routes.payment_routes import payment_bp, init_payment_service

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    jwt.init_app(app)

    init_payment_service(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp, url_prefix='/payments')

    return app