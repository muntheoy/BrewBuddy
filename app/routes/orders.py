from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Order, Product, OrderProducts, User, Payment
from ..extensions import db
from datetime import datetime
from typing import Dict, Any, List
from functools import wraps

orders_bp = Blueprint('orders', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({"msg": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

@orders_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """
    Создание нового заказа
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()

    product_ids = data.get('product_ids')
    quantities = data.get('quantities')
    
    if not product_ids or not quantities or len(product_ids) != len(quantities):
        return jsonify({"msg": "Invalid order details"}), 400

    try:
        total_amount = 0
        products = Product.query.filter(Product.product_id.in_(product_ids)).all()
        
        if len(products) != len(product_ids):
            return jsonify({"msg": "Some products not found"}), 404

        # Проверяем наличие товаров
        for i, product in enumerate(products):
            if product.stock_quantity < quantities[i]:
                return jsonify({
                    "msg": f"Not enough stock for product {product.name}",
                    "product_id": product.product_id,
                    "available": product.stock_quantity,
                    "requested": quantities[i]
                }), 400

        # Создаем заказ
        order = Order(
            user_id=current_user_id,
            status='pending',
            payment_status='pending',
            total_amount=0
        )
        db.session.add(order)
        db.session.commit()

        # Добавляем товары в заказ
        for i, product in enumerate(products):
            quantity = quantities[i]
            total_amount += float(product.price) * quantity
            
            # Уменьшаем количество товара на складе
            product.stock_quantity -= quantity
            
            order_product = OrderProducts(
                order_id=order.order_id,
                product_id=product.product_id,
                quantity=quantity
            )
            db.session.add(order_product)

        order.total_amount = total_amount
        db.session.commit()

        return jsonify({
            "msg": "Order created successfully",
            "order": {
                "order_id": order.order_id,
                "total_amount": float(order.total_amount),
                "status": order.status,
                "payment_status": order.payment_status,
                "created_at": order.created_at.isoformat()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400

@orders_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_user_orders():
    """
    Получение списка заказов пользователя
    """
    current_user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=current_user_id).all()
    
    orders_data = []
    for order in orders:
        order_products = OrderProducts.query.filter_by(order_id=order.order_id).all()
        products_data = []
        
        for op in order_products:
            product = Product.query.get(op.product_id)
            products_data.append({
                "product_id": product.product_id,
                "name": product.name,
                "price": float(product.price),
                "quantity": op.quantity
            })
            
        orders_data.append({
            "order_id": order.order_id,
            "total_amount": float(order.total_amount),
            "status": order.status,
            "payment_status": order.payment_status,
            "created_at": order.created_at.isoformat(),
            "products": products_data
        })
    
    return jsonify({"orders": orders_data})

@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id: int):
    """
    Получение информации о конкретном заказе
    """
    current_user_id = get_jwt_identity()
    order = Order.query.get_or_404(order_id)
    
    order_products = OrderProducts.query.filter_by(order_id=order_id).all()
    products_data = []
    
    for op in order_products:
        product = Product.query.get(op.product_id)
        products_data.append({
            "product_id": product.product_id,
            "name": product.name,
            "price": float(product.price),
            "quantity": op.quantity
        })
    
    # Получаем информацию о платеже, если он есть
    payment = Payment.query.filter_by(order_id=order_id).first()
    payment_data = payment.to_dict() if payment else None
    
    return jsonify({
        "order_id": order.order_id,
        "total_amount": float(order.total_amount),
        "status": order.status,
        "payment_status": order.payment_status,
        "created_at": order.created_at.isoformat(),
        "products": products_data,
        "payment": payment_data
    })

@orders_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id: int):
    """
    Отмена заказа
    """
    current_user_id = get_jwt_identity()
    order = Order.query.get_or_404(order_id)
    
    # Проверяем, можно ли отменить заказ
    if order.status not in ['pending', 'processing']:
        return jsonify({"msg": "Order cannot be cancelled"}), 400
    
    try:
        # Возвращаем товары на склад
        order_products = OrderProducts.query.filter_by(order_id=order_id).all()
        for op in order_products:
            product = Product.query.get(op.product_id)
            product.stock_quantity += op.quantity
        
        order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({"msg": "Order cancelled successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400