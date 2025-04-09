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