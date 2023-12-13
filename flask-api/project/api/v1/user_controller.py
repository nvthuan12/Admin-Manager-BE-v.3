from flask import Blueprint, request, jsonify
from project import app, db
from werkzeug.exceptions import Conflict, InternalServerError, NotFound, BadRequest, Unauthorized
from project.models.user import User
from project.models.role import Role
from project.models.role_has_permission import RoleHasPermission
from project.models.permission import Permission
from project.models.user_has_role import UserHasRole
from flask_jwt_extended import jwt_required, get_jwt_identity
from project.api.v1.has_permission import has_permission
from project.services.user_service import UserService
from project.api.common.base_response import BaseResponse
from datetime import datetime
from project.services.send_mail import Schedule_mail

user_blueprint = Blueprint('user', __name__)


@user_blueprint.route('/users', methods=['GET'])
@jwt_required()
@has_permission("view")
def view_list_user():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        result = UserService.get_list_users(page, per_page)
        return BaseResponse.success(result)
    except Exception as e:
        raise InternalServerError('Internal Server Error') from e


@user_blueprint.route('/users', methods=['POST'])
@jwt_required()
@has_permission("create")
def create_user():
    try:
        data = request.get_json()
        response = UserService.add_new_user(data)
        return response
    except Conflict as e:
        return BaseResponse.error(e)
    except Exception as e:
        return BaseResponse.error_validate(e)


@user_blueprint.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@has_permission('update')
def update_user(user_id):
    try:
        data = request.get_json()
        response = UserService.update_user(data, user_id)
        return response
    except NotFound as e:
        return BaseResponse.error(e)
    except Conflict as e:
        return BaseResponse.error(e)
    except Exception as e:
        return BaseResponse.error_validate(e)

@user_blueprint.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@has_permission("delete")
def delete_user(user_id):
    try:
        response = UserService.delete_user(user_id)
        return response
    except NotFound as e:
        return BaseResponse.error(e)
    except Exception as e:
        raise InternalServerError() from e

@user_blueprint.route('/users/change_password', methods=['PUT'])
@jwt_required()
@has_permission("update")
def change_password():
    try:
        data = request.get_json()
        response = UserService.change_password(data)
        return response
    except NotFound as e:
        return BaseResponse.error(e)
    except BadRequest as e:
        return BaseResponse.error(e)
    except Unauthorized as e:
        return BaseResponse.error(e)
    except Exception as e:
        return BaseResponse.error_validate(e)
    
@user_blueprint.route('/users/profile', methods=['PUT'])
@jwt_required()
@has_permission("update")
def edit_profile():
    try:
        data = request.get_json()
        response = UserService.edit_profile(data)
        return response
    except NotFound as e:
        return BaseResponse.error(e)
    except Conflict as e:
        return BaseResponse.error(e)
    except Exception as e:
        return BaseResponse.error_validate(e)

@user_blueprint.route('/users/search', methods=['GET'])
@jwt_required()
@has_permission("view")
def search_user_by_name_or_email():
    try:
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        response = UserService.search_list_user(page,per_page,search)

        return response
    except NotFound as e:
        raise BaseResponse.error(e)
    except Exception as e:
        raise InternalServerError('Internal Server Error') from e
    
@user_blueprint.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@has_permission("view")
def get_detail_user(user_id):
    try:
        user=UserService.detail_user(user_id)
        return BaseResponse.success(user)
    except NotFound as e:
        raise BaseResponse.error(e)
    except Exception as e:
        raise InternalServerError(e) 
    
@user_blueprint.route('/test', methods=['POST'])
# @jwt_required()
# @has_permission("view")
def push():
 
    user= User.query.get(1)
    Schedule_mail.send_notification_to_users(user)
    return "success"