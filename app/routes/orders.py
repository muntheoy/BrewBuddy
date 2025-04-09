from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Order, Product, OrderProducts, User
from ..extensions import db

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/order', methods=['POST'])
@jwt_required()
def place_order():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    product_ids = data.get('product_ids')
    quantities = data.get('quantities')
    
    if not product_ids or not quantities or len(product_ids) != len(quantities):
        return jsonify({"msg": "Invalid order details"}), 400

    total_amount = 0
    products = Product.query.filter(Product.product_id.in_(product_ids)).all()

    order = Order(user_id=current_user_id, total_amount=total_amount)
    db.session.add(order)
    db.session.commit()

    for i, product in enumerate(products):
        quantity = quantities[i]
        total_amount += product.price * quantity
        order_product = OrderProducts(order_id=order.order_id, product_id=product.product_id, quantity=quantity)
        db.session.add(order_product)

    order.total_amount = total_amount
    db.session.commit()

    return jsonify({"msg": "Order placed successfully", "order_id": order.order_id})