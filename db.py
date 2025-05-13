from app import create_app, db
from app.models import User, Order, Product, OrderProducts

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db() 