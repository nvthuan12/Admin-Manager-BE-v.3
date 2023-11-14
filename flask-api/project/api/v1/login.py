from flask import Blueprint, request, jsonify
import project.api.common.utils.exceptions as exceptions
from project import app,db
from project.models.user import User
from project.models.role import Role
from project.models.role_has_permission import RoleHasPermission
from project.models.permission import Permission
from project.models.user_has_role import UserHasRole
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, set_access_cookies, unset_jwt_cookies,get_jwt_identity,get_jwt
from project.api.v1.has_permission import has_permission, get_role_names

login_blueprint = Blueprint('login', __name__)

@login_blueprint.route('/login', methods=['POST'])
def login():
    post_data = request.get_json()
    if not post_data:
        return exceptions.NO_INPUT_400
    email = post_data.get('email', None)
    password = post_data.get('password', None)

    if not email or not password:
        return exceptions.INVALID_INPUT_422

    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return exceptions.UNAUTHORIZED_401
    access_token = create_access_token(identity=user.user_id )
    role_name=get_role_names(user.user_id)

    return jsonify(access_token=access_token,role_name=role_name),200

@login_blueprint.route('/home',methods=['GET'])
@jwt_required()
@has_permission("view")
def home():
    return "hello"

