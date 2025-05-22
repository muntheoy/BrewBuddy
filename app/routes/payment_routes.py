from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.payment_service import PaymentService
from app.extensions import db
from app.models import Order, Payment, User
from datetime import datetime
from typing import Dict, Any

payment_bp = Blueprint('payments', __name__)
payment_service = PaymentService()

def init_payment_service(app):
    payment_service.init_app(app)

@payment_bp.route('/create', methods=['POST'])
@jwt_required()
def create_payment():
    """
    Создает новый платеж для заказа
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'order_id' not in data:
        return jsonify({'error': 'Missing order_id'}), 400
        
    order_id = data['order_id']
    
    order = Order.query.get_or_404(order_id)
        
    if order.payment_status == 'succeeded':
        return jsonify({'error': 'Order is already paid'}), 400
        
    active_payment = Payment.query.filter_by(
        order_id=order_id,
        status='pending'
    ).first()
    
    if active_payment:
        return jsonify({
            'error': 'Active payment already exists',
            'payment_id': active_payment.payment_id,
            'confirmation_url': active_payment.payment_details.get('confirmation_url')
        }), 400
    
    try:
        payment_info = payment_service.create_payment(
            amount=float(order.total_amount),
            description=f'Payment for order {order_id}',
            order_id=order_id
        )
        
        payment = Payment(
            payment_id=payment_info['id'],
            order_id=order_id,
            user_id=current_user_id,
            amount=order.total_amount,
            currency='RUB',
            status='pending',
            payment_method=payment_info.get('payment_method', 'card'),
            payment_details={
                'confirmation_url': payment_info['confirmation']['confirmation_url'],
                'payment_method': payment_info.get('payment_method'),
                'created_at': datetime.utcnow().isoformat()
            }
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'payment_id': payment_info['id'],
            'confirmation_url': payment_info['confirmation']['confirmation_url'],
            'amount': float(order.total_amount),
            'currency': 'RUB'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/<string:payment_id>', methods=['GET'])
@jwt_required()
def get_payment_status(payment_id: str):
    """
    Получает статус платежа
    """
    current_user_id = get_jwt_identity()
    payment = Payment.query.filter_by(payment_id=payment_id).first_or_404()
    
    try:
        payment_info = payment_service.verify_payment(payment_id)
        
        if payment_info:
            payment.status = payment_info['status']
            
            if payment_info['status'] == 'succeeded':
                payment.paid_at = datetime.utcnow()
                order = Order.query.get(payment.order_id)
                if order:
                    order.payment_status = 'succeeded'
                    order.status = 'processing'
            
            db.session.commit()
            
        return jsonify({
            'payment_id': payment.payment_id,
            'status': payment.status,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'payment_method': payment.payment_method,
            'created_at': payment.created_at.isoformat(),
            'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/<string:payment_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_payment(payment_id: str):
    """
    Отменяет платеж
    """
    current_user_id = get_jwt_identity()
    payment = Payment.query.filter_by(payment_id=payment_id).first_or_404()
    
    if payment.status not in ['pending']:
        return jsonify({'error': 'Payment cannot be cancelled'}), 400
    
    try:
        payment_info = payment_service.cancel_payment(payment_id)
        
        if payment_info:
            payment.status = 'cancelled'
            if not payment.payment_details or not isinstance(payment.payment_details, dict):
                payment.payment_details = {}
            payment.payment_details['cancelled_at'] = datetime.utcnow().isoformat()
            db.session.commit()
            
        return jsonify({
            'payment_id': payment.payment_id,
            'status': payment.status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500