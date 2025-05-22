from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Product, User
from ..extensions import db

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    products = Product.query.all()
    return jsonify({
        "products": [{"product_id": p.product_id, "name": p.name, "price": str(p.price)} for p in products]
    })

@products_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    if not name or price is None:
        return jsonify({'error': 'Name and price required'}), 400
    product = Product(name=name, price=price)
    db.session.add(product)
    db.session.commit()
    return jsonify({'msg': 'Product created', 'product_id': product.product_id}), 201

@products_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    stock_quantity = data.get('stock_quantity')

    if name:
        product.name = name
    if price is not None:
        product.price = price
    if stock_quantity is not None:
        product.stock_quantity = stock_quantity

    db.session.commit()
    return jsonify({'msg': 'Product updated'})

@products_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'msg': 'Product deleted'})