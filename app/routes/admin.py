from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, Product, Order, OrderProducts
from ..extensions import db
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({"msg": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin', methods=['GET'])
@jwt_required()
@admin_required
def admin_panel():
    users = User.query.all()
    products = Product.query.all()

    return jsonify({
        "users": [{"user_id": u.user_id, "username": u.username, "role": u.role} for u in users],
        "products": [{"product_id": p.product_id, "name": p.name, "price": str(p.price)} for p in products]
    })

@admin_bp.route('/products', methods=['POST'])
@jwt_required()
@admin_required
def create_product():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    required_fields = ['name', 'price']
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "Missing required fields"}), 400

    try:
        new_product = Product(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            category_id=data.get('category_id'),
            image_url=data.get('image_url'),
            stock_quantity=data.get('stock_quantity', 0),
            created_by=current_user_id
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify({
            "msg": "Product created successfully",
            "product": new_product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400

@admin_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_product(product_id):
    data = request.get_json()
    product = Product.query.get_or_404(product_id)
    
    try:
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'category_id' in data:
            product.category_id = data['category_id']
        if 'image_url' in data:
            product.image_url = data['image_url']
        if 'stock_quantity' in data:
            product.stock_quantity = data['stock_quantity']
        if 'is_active' in data:
            product.is_active = data['is_active']
            
        db.session.commit()
        
        return jsonify({
            "msg": "Product updated successfully",
            "product": product.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400

@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"msg": "Product deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400

@admin_bp.route('/products', methods=['GET'])
@jwt_required()
@admin_required
def get_products():
    products = Product.query.all()
    return jsonify({
        "products": [product.to_dict() for product in products]
    })

@admin_bp.route('/products/<int:product_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@admin_bp.route('/admin/orders', methods=['GET'])
@jwt_required()
@admin_required
def get_orders():
    orders = Order.query.all()
    orders_data = []
    for order in orders:
        order_data = {
            "order_id": order.order_id,
            "user_id": order.user_id,
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at,
            "total_amount": str(order.total_amount)
        }

        order_products = OrderProducts.query.filter_by(order_id=order.order_id).all()
        products = []
        for order_product in order_products:
            product = Product.query.get(order_product.product_id)
            if product:
                products.append({
                    "product_id": product.product_id,
                    "name": product.name,
                    "price": str(product.price),
                    "quantity": order_product.quantity
                })

        order_data["products"] = products
        orders_data.append(order_data)

    return jsonify({
        "orders": orders_data
    })

@admin_bp.route('/admin/change_order_status/<int:order_id>', methods=['POST'])
@jwt_required()
@admin_required
def change_order_status(order_id):
    data = request.get_json()

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"msg": "Order not found"}), 404

    order.status = data.get('status', order.status)
    db.session.commit()

    return jsonify({"msg": "Order status updated"}), 200