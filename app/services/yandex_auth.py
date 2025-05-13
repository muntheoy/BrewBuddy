from typing import Dict, Any, Optional
import requests
from jose import jwt
from datetime import datetime, timedelta
from app import db
from app.models import User

class YandexAuthService:
    def __init__(self) -> None:
        self.client_id: str = ""
        self.client_secret: str = ""
        self.token_url: str = "https://oauth.yandex.ru/token"
        self.userinfo_url: str = "https://login.yandex.ru/info"
        self.jwt_secret: str = "your-secret-key"

    def get_access_token(self, code: str) -> Dict[str, Any]:
        data: Dict[str, str] = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.token_url, data=data)
        return response.json()

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        headers: Dict[str, str] = {"Authorization": f"OAuth {access_token}"}
        response = requests.get(self.userinfo_url, headers=headers)
        return response.json()

    def create_or_update_user(self, yandex_user_info: Dict[str, Any]) -> User:
        user: Optional[User] = User.query.filter_by(yandex_id=yandex_user_info["id"]).first()
        
        if not user:
            user = User.query.filter_by(email=yandex_user_info["default_email"]).first()
            if user:
                user.yandex_id = yandex_user_info["id"]
            else:
                user = User(
                    yandex_id=yandex_user_info["id"],
                    email=yandex_user_info["default_email"],
                    first_name=yandex_user_info.get("first_name", ""),
                    last_name=yandex_user_info.get("last_name", ""),
                    username=yandex_user_info.get("default_email", "").split("@")[0]
                )
                db.session.add(user)
        else:
            user.email = yandex_user_info["default_email"]
            user.first_name = yandex_user_info.get("first_name", "")
            user.last_name = yandex_user_info.get("last_name", "")
        
        db.session.commit()
        return user

    def create_jwt_token(self, user: User) -> str:
        payload: Dict[str, Any] = {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            "is_yandex_user": user.is_yandex_user,
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256") 