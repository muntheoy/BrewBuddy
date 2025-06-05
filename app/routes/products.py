from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Product, User
from ..extensions import db
from ..services.file_service import save_file
from werkzeug.utils import secure_filename
import os

products_bp = Blueprint('products', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@products_bp.route('/products', methods=['GET'])
@jwt_required()
def get_products():
    products = Product.query.all()
    return jsonify({
        "products": [{
            "product_id": p.product_id,
            "name": p.name,
            "price": str(p.price),
            "image_url": p.image_url
        } for p in products]
    })

@products_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    # Проверяем наличие файла
    if 'image' not in request.files:
        return jsonify({'error': 'Image file is required'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Получаем остальные данные продукта
    name = request.form.get('name')
    price = request.form.get('price')
    
    if not name or price is None:
        return jsonify({'error': 'Name and price required'}), 400

    try:
        # Сохраняем изображение
        image_url = save_file(file)
        
        # Создаем продукт
        product = Product(
            name=name,
            price=price,
            image_url=image_url
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'msg': 'Product created',
            'product_id': product.product_id,
            'image_url': image_url
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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