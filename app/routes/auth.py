from typing import Dict, Any, Tuple, Union
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from ..models import User
from ..extensions import db
from app.services.yandex_auth import YandexAuthService

auth_bp = Blueprint('auth', __name__)
yandex_auth = YandexAuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = generate_password_hash(data.get('password'))
    role = data.get('role', 'customer')

    if not username or not data.get('password'):
        return jsonify({"msg": "Username and password are required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"msg": "User already exists"}), 400

    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=str(new_user.user_id))
    refresh_token = create_refresh_token(identity=str(new_user.user_id))

    return jsonify({
        "msg": "User registered successfully",
        "access_token": access_token,
        "refresh_token": refresh_token
    })

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.user_id))
        refresh_token = create_refresh_token(identity=str(user.user_id))

        return jsonify({
            "msg": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    
    return jsonify({"msg": "Invalid credentials"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({"msg": "Logout successful"}), 200

@auth_bp.route('/auth/yandex/callback', methods=['POST'])
def yandex_callback() -> Tuple[Dict[str, Any], int]:
    data: Dict[str, Any] = request.get_json()
    code: str = data.get('code')
    
    if not code:
        return jsonify({'error': 'Code is required'}), 400
    
    try:
        token_response: Dict[str, Any] = yandex_auth.get_access_token(code)
        
        if 'error' in token_response:
            if token_response['error'] == 'invalid_grant':
                return jsonify({'error': 'Wrong authorization code received from YaID'}), 400
            elif token_response['error'] == 'bad_verification_code':
                return jsonify({'error': 'Authorization code is invalid or expired'}), 400
            return jsonify({'error': token_response['error']}), 400
        
        access_token: str = token_response['access_token']
        user_info: Dict[str, Any] = yandex_auth.get_user_info(access_token)
        user = yandex_auth.create_or_update_user(user_info)
        jwt_token: str = yandex_auth.create_jwt_token(user)
        
        return jsonify({
            'access_token': jwt_token,
            'user': {
                'user_id': user.user_id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_yandex_user': user.is_yandex_user
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500