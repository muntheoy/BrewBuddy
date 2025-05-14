from flask import Blueprint, request, jsonify, current_app
from app.services.payment_service import PaymentService
from app.extensions import db
from app.models import Order, Payment
import uuid

bp = Blueprint('payments', __name__)
payment_service = PaymentService()

def init_payment_service(app):
    payment_service.init_app(app)

@bp.route('/create', methods=['POST'])
def create_payment():
    """
    Создает новый платеж для заказа
    """
    data = request.get_json()
    
    if not data or 'order_id' not in data or 'amount' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    order_id = data['order_id']
    amount = float(data['amount'])
    description = data.get('description', f'Payment for order {order_id}')
    
    try:
        payment_info = payment_service.create_payment(
            amount=amount,
            description=description,
            order_id=order_id
        )
        
        payment = Payment(
            order_id=order_id,
            payment_id=payment_info['id'],
            amount=amount,
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'payment_id': payment_info['id'],
            'confirmation_url': payment_info['confirmation']['confirmation_url']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/verify', methods=['GET'])
def verify_payment():
    """
    Проверяет статус платежа после возврата пользователя с YooMoney
    """
    payment_id = request.args.get('payment_id')
    
    if not payment_id:
        return jsonify({'error': 'Missing payment_id'}), 400
        
    try:
        payment_info = payment_service.verify_payment(payment_id)
        
        if not payment_info:
            return jsonify({'error': 'Payment not found'}), 404
            
        payment = Payment.query.filter_by(payment_id=payment_id).first()
        if payment:
            payment.status = payment_info['status']
            db.session.commit()
            
        return jsonify({
            'status': payment_info['status'],
            'amount': payment_info['amount']['value'],
            'currency': payment_info['amount']['currency']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 