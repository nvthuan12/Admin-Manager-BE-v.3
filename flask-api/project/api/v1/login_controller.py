from flask import Blueprint, request, jsonify
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized
from project import app,db
from project.models.user import User
from project.models.role import Role
from project.models.role_has_permission import RoleHasPermission
from project.models.permission import Permission
from project.models.user_has_role import UserHasRole
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, set_access_cookies, unset_jwt_cookies,get_jwt_identity,get_jwt
from datetime import timedelta
from project.api.v1.has_permission import has_permission, get_role_names

login_blueprint = Blueprint('login', __name__)

@login_blueprint.route('/form', methods=['OPTIONS'])  
def handle_preflight():
    response = app.make_default_options_response()
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@login_blueprint.route('/login', methods=['POST'])
def login():
    post_data = request.get_json()
    if not post_data:
        raise BadRequest('Invalid input data.')

    email = post_data.get('email')
    password = post_data.get('password')

    if not email or not password:
        raise BadRequest('Email and password are required.')

    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        raise Unauthorized('Invalid email or password.')

    access_token = create_access_token(identity=user.user_id, expires_delta=timedelta(days=1))
    role_name = get_role_names(user.user_id)
    response = jsonify(message='Logged in successfully', access_token=access_token, role_name=role_name)
    set_access_cookies(response, access_token)
    return response, 200

@login_blueprint.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    response = jsonify(message='Logout successfully')
    unset_jwt_cookies(response)
    return response, 200
