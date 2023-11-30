from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, Unauthorized
from project import app, db
from project.services.login_service import AuthService
from flask_jwt_extended import jwt_required, create_access_token, set_access_cookies, unset_jwt_cookies, get_jwt_identity, get_jwt
from datetime import timedelta
from project.api.common.base_response import BaseResponse

login_blueprint = Blueprint('login', __name__)


@login_blueprint.route('/form', methods=['OPTIONS'])
def handle_preflight():
    response = app.make_default_options_response()
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


@login_blueprint.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user = AuthService.authenticate_user(email, password)
        response = AuthService.login_user(user)
        return BaseResponse.success(response, "success", 200)
    except BadRequest as e:
        return BaseResponse.error(e)
    except Unauthorized as e:
        return BaseResponse.error(e)


@login_blueprint.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    response = jsonify(message='Logout successfully')
    unset_jwt_cookies(response)
    return response, 200
