from typing import Dict, Any, Optional, Tuple
import requests
from datetime import datetime, timedelta
from app import db
from app.models import User
from flask_jwt_extended import create_access_token, get_jwt_identity

class YandexAuthService:
    def __init__(self) -> None:
        self.client_id: str = "96d622e3132846ed89e685c5cdd109ef"
        self.client_secret: str = "6b2af9713e684c9094e7ff32ca8e8708"
        self.token_url: str = "https://oauth.yandex.ru/token"
        self.userinfo_url: str = "https://login.yandex.ru/info"
        self.redirect_uri: str = "http://localhost:5000/auth/yandex/callback"

    def get_access_token(self, code: str) -> Dict[str, Any]:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        try:
            response = requests.post(self.token_url, data=data)
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        headers = {
            'Authorization': f'OAuth {access_token}'
        }
        try:
            response = requests.get(self.userinfo_url, headers=headers)
            return response.json()
        except Exception as e:
            return {'error': str(e)}

    def create_or_update_user(self, user_info: Dict[str, Any], current_user_id: Optional[int] = None) -> Tuple[User, bool]:
        """
        Создает нового пользователя или обновляет существующего
        :param user_info: Информация о пользователе от Яндекс
        :param current_user_id: ID текущего пользователя (если есть)
        :return: Tuple[User, bool] - (пользователь, является ли новым)
        """
        yandex_id = user_info.get('id')
        email = user_info.get('default_email')
        
        # Если есть текущий пользователь, привязываем к нему Яндекс
        if current_user_id:
            user = User.query.get(current_user_id)
            if user:
                user.yandex_id = yandex_id
                db.session.commit()
                return user, False
        
        # Ищем пользователя по Яндекс ID
        user = User.query.filter_by(yandex_id=yandex_id).first()
        if user:
            return user, False
            
        # Ищем пользователя по email
        user = User.query.filter_by(email=email).first()
        if user:
            user.yandex_id = yandex_id
            db.session.commit()
            return user, False
            
        # Создаем нового пользователя
        new_user = User(
            yandex_id=yandex_id,
            email=email,
            first_name=user_info.get('first_name'),
            last_name=user_info.get('last_name'),
            username=email.split('@')[0],  # Используем часть email до @ как username
            role='customer'
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user, True

    def create_jwt_token(self, user: User) -> str:
        access_token = create_access_token(
            identity=str(user.user_id),
            expires_delta=timedelta(days=7)
        )
        user.update_tokens(access_token, None)  # Для Яндекс авторизации refresh token не нужен
        return access_token

    def validate_token(self, user: User) -> bool:
        return user.is_token_valid

    def refresh_token_if_needed(self, user: User) -> Optional[str]:
        if not user.is_token_valid:
            new_token = create_access_token(
                identity=str(user.user_id),
                expires_delta=timedelta(days=7)
            )
            user.update_tokens(new_token, None)
            return new_token
        return None 