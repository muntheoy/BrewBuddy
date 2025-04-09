from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, Product, Order, OrderProducts
from ..extensions import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin', methods=['GET'])
@jwt_required()
def admin_panel():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user.role != 'admin':
        return jsonify({"msg": "Access denied: Admins only"}), 403

    users = User.query.all()
    products = Product.query.all()

    return jsonify({
        "users": [{"user_id": u.user_id, "username": u.username, "role": u.role} for u in users],
        "products": [{"product_id": p.product_id, "name": p.name, "price": str(p.price)} for p in products]
    })

@admin_bp.route('/admin/add_product', methods=['POST'])
@jwt_required()
def add_product():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user.role != 'admin':
        return jsonify({"msg": "Access denied: Admins only"}), 403

    data = request.get_json()

    name = data.get('name')
    price = data.get('price')
    category_id = data.get('category_id')

    if not name or not price or not category_id:
        return jsonify({"msg": "Missing product details"}), 400

    new_product = Product(name=name, price=price, category_id=category_id)
    db.session.add(new_product)
    db.session.commit()

    return jsonify({"msg": "Product added successfully"}), 201

@admin_bp.route('/admin/edit_product/<int:product_id>', methods=['POST'])
@jwt_required()
def edit_product(product_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user.role != 'admin':
        return jsonify({"msg": "Access denied: Admins only"}), 403

    data = request.get_json()

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404

    name = data.get('name')
    price = data.get('price')
    category_id = data.get('category_id')

    if name:
        product.name = name
    if price:
        product.price = price
    if category_id:
        product.category_id = category_id

    db.session.commit()

    return jsonify({"msg": "Product updated successfully"}), 200

@admin_bp.route('/admin/delete_product/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user.role != 'admin':
        return jsonify({"msg": "Access denied: Admins only"}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"msg": "Product not found"}), 404

    order_products = OrderProducts.query.filter_by(product_id=product_id).all()
    for order_product in order_products:
        db.session.delete(order_product)

    db.session.delete(product)
    db.session.commit()

    return jsonify({"msg": "Product deleted successfully"}), 200

@admin_bp.route('/admin/orders', methods=['GET'])
@jwt_required()
def get_orders():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user.role != 'admin':
        return jsonify({"msg": "Access denied: Admins only"}), 403

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
def change_order_status(order_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user.role != 'admin':
        return jsonify({"msg": "Access denied: Admins only"}), 403

    data = request.get_json()

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"msg": "Order not found"}), 404

    order.status = data.get('status', order.status)
    db.session.commit()

    return jsonify({"msg": "Order status updated"}), 200