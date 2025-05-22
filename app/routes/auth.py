from typing import Dict, Any, Tuple, Union
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from ..models import User
from ..extensions import db
from app.services.yandex_auth import YandexAuthService
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)
yandex_auth = YandexAuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')
    first_name = data.get('first_name')
    last_name = data.get('last_name')

    if not email or not password:
        return jsonify({"msg": "Email and password are required"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"msg": "User already exists"}), 400

    new_user = User(
        email=email,
        password=generate_password_hash(password),
        username=username,
        first_name=first_name,
        last_name=last_name,
        role='customer'
    )
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=str(new_user.user_id), expires_delta=timedelta(days=7))
    refresh_token = create_refresh_token(identity=str(new_user.user_id), expires_delta=timedelta(days=30))
    
    new_user.update_tokens(access_token, refresh_token)

    return jsonify({
        "msg": "User registered successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "user_id": new_user.user_id,
            "email": new_user.email,
            "username": new_user.username,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "role": new_user.role
        }
    })

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.user_id), expires_delta=timedelta(days=7))
        refresh_token = create_refresh_token(identity=str(user.user_id), expires_delta=timedelta(days=30))
        
        user.update_tokens(access_token, refresh_token)

        return jsonify({
            "msg": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role
            }
        })
    
    return jsonify({"msg": "Invalid credentials"}), 401

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"msg": "User not found"}), 404

    access_token = create_access_token(identity=str(user.user_id), expires_delta=timedelta(days=7))
    user.update_tokens(access_token, user.refresh_token)

    return jsonify({
        "access_token": access_token,
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role
        }
    })

@auth_bp.route('/auth/yandex/callback', methods=['POST'])
def yandex_callback() -> Tuple[Dict[str, Any], int]:
    data: Dict[str, Any] = request.get_json()
    code: str = data.get('code')
    current_user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            current_user_id = int(get_jwt_identity())
        except:
            pass
    if not code:
        return jsonify({'error': 'Code is required'}), 400
    try:
        token_response: Dict[str, Any] = yandex_auth.get_access_token(code)
        if not token_response or not isinstance(token_response, dict):
            return jsonify({'error': 'Yandex did not return a valid response'}), 500
        if 'error' in token_response:
            if token_response['error'] == 'invalid_grant':
                return jsonify({'error': 'Wrong authorization code received from YaID'}), 400
            elif token_response['error'] == 'bad_verification_code':
                return jsonify({'error': 'Authorization code is invalid or expired'}), 400
            return jsonify({'error': token_response['error']}), 400
        access_token: str = token_response['access_token']
        user_info: Dict[str, Any] = yandex_auth.get_user_info(access_token)
        email = user_info.get('default_email')
        user = User.query.filter_by(email=email).first()
        if not user:
            # Пользователь не найден — просим пароль
            return jsonify({
                'need_password': True,
                'profile': {
                    'email': email,
                    'first_name': user_info.get('first_name'),
                    'last_name': user_info.get('last_name'),
                    'yandex_id': user_info.get('id'),
                    'username': email.split('@')[0]
                }
            }), 200
        # Если пользователь есть — обычная логика
        user, is_new = yandex_auth.create_or_update_user(user_info, current_user_id)
        jwt_token: str = yandex_auth.create_jwt_token(user)
        response = {
            'access_token': jwt_token,
            'user': {
                'user_id': user.user_id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_yandex_user': user.is_yandex_user
            }
        }
        if is_new:
            response['msg'] = 'New user created and linked with Yandex'
        else:
            response['msg'] = 'Existing user linked with Yandex'
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/yandex/register', methods=['POST'])
def yandex_register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    yandex_id = data.get('yandex_id')
    username = data.get('username')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 400
    new_user = User(
        email=email,
        password=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        yandex_id=yandex_id,
        username=username,
        role='customer'
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'msg': 'User created successfully'}), 201