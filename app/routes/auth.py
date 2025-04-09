from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from ..models import User
from ..extensions import db

auth_bp = Blueprint('auth', __name__)

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