from datetime import datetime, timedelta
from app import db

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=False, default='customer')
    yandex_id = db.Column(db.String(100), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    access_token = db.Column(db.String(500), nullable=True)
    refresh_token = db.Column(db.String(500), nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'

    @property
    def is_yandex_user(self):
        return self.yandex_id is not None

    def update_tokens(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = datetime.utcnow() + timedelta(days=7)
        db.session.commit()

    @property
    def is_token_valid(self):
        return self.token_expires_at and self.token_expires_at > datetime.utcnow()

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    status = db.Column(db.String(50))
    payment_status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    total_amount = db.Column(db.Numeric(10, 2))

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.String(100))
    image_url = db.Column(db.String(500))  # URL изображения в S3
    stock_quantity = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'category_id': self.category_id,
            'image_url': self.image_url,
            'stock_quantity': self.stock_quantity,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class OrderProducts(db.Model):
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), primary_key=True)
    quantity = db.Column(db.Integer, default=1)

class Payment(db.Model):
    payment_id = db.Column(db.String(100), primary_key=True)  # ID платежа в YooMoney
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    amount = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(3), default='RUB')
    status = db.Column(db.String(50))  # pending, succeeded, canceled
    payment_method = db.Column(db.String(50))  # card, bank_transfer, etc.
    payment_details = db.Column(db.JSON)  # Дополнительные детали платежа
    error_code = db.Column(db.String(100))
    error_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Payment {self.payment_id}>'

    def to_dict(self):
        return {
            'payment_id': self.payment_id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_details': self.payment_details,
            'error_code': self.error_code,
            'error_description': self.error_description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }