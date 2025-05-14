from yookassa import Configuration, Payment as YooPayment
from flask import current_app
from typing import Dict, Optional

class PaymentService:
    def __init__(self):
        self.api_key = None
        self.return_url = None
        self.test_mode = None

    def init_app(self, app):
        """Initialize the service with app configuration"""
        self.api_key = app.config['YOOMONEY_API_KEY']
        self.return_url = app.config['YOOMONEY_RETURN_URL']
        self.test_mode = app.config['YOOMONEY_TEST_MODE']
        
        Configuration.account_id = app.config['YOOMONEY_SHOP_ID']
        Configuration.secret_key = self.api_key

    def create_payment(self, amount: float, description: str, order_id: str) -> Dict:
        """
        Создает новый платеж в YooMoney
        
        Args:
            amount: Сумма платежа
            description: Описание платежа
            order_id: ID заказа в нашей системе
            
        Returns:
            Dict с информацией о созданном платеже
        """
        if not self.api_key:
            raise RuntimeError("PaymentService not initialized. Call init_app first.")
            
        payment = YooPayment.create({
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": self.return_url
            },
            "capture": True,
            "description": description,
            "metadata": {
                "order_id": order_id
            }
        }, idempotency_key=order_id)
        
        return {
            'id': payment.id,
            'status': payment.status,
            'amount': {
                'value': payment.amount.value,
                'currency': payment.amount.currency
            },
            'confirmation': {
                'type': payment.confirmation.type,
                'confirmation_url': payment.confirmation.confirmation_url
            },
            'created_at': payment.created_at,
            'description': payment.description,
            'metadata': payment.metadata
        }

    def verify_payment(self, payment_id: str) -> Optional[Dict]:
        """
        Проверяет статус платежа в YooMoney
        
        Args:
            payment_id: ID платежа в YooMoney
            
        Returns:
            Dict с информацией о платеже или None, если платеж не найден
        """
        if not self.api_key:
            raise RuntimeError("PaymentService not initialized. Call init_app first.")
            
        try:
            payment = YooPayment.find_one(payment_id)
            
            return {
                'id': payment.id,
                'status': payment.status,
                'amount': {
                    'value': payment.amount.value,
                    'currency': payment.amount.currency
                },
                'created_at': payment.created_at,
                'description': payment.description,
                'metadata': payment.metadata
            }
        except Exception as e:
            if "Payment not found" in str(e):
                return None
            raise e 