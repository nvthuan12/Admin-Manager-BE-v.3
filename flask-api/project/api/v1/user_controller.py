from flask import Blueprint, request, jsonify
from project import app, db
from werkzeug.exceptions import BadRequest, Conflict, InternalServerError, NotFound
from project.models.user import User
from project.models.role import Role
from project.models.role_has_permission import RoleHasPermission
from project.models.permission import Permission
from project.models.user_has_role import UserHasRole
from project.models.booking_user import BookingUser
from flask_jwt_extended import jwt_required
from collections import defaultdict
from project.api.v1.has_permission import has_permission
from project.services.user_service import UserService
from project.api.common.base_response import BaseResponse
from datetime import datetime

user_blueprint = Blueprint('user', __name__)

@user_blueprint.route('/users', methods=['GET'])
@jwt_required()
@has_permission("view")
def view_list_user():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        result = UserService.get_paginated_users(page, per_page)
        return BaseResponse.success(result)
    except Exception as e:
        return BaseResponse.error(e)

@user_blueprint.route('/users', methods=['POST'])
@jwt_required()
@has_permission("create")
def create_user():
    data = request.get_json()
    user_name = data.get('user_name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    password = data.get('password')
    role_ids= data.get('role_id')
    new_user = User(
        user_name=user_name,
        email=email,
        phone_number=phone_number,
        password=password,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_deleted=False
    )
    validate_error=new_user.validate_all_fields()
 
    if validate_error:
        return jsonify({"errors": validate_error})
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        raise Conflict("Email already exists")

    existing_phone = User.query.filter_by(phone_number=phone_number).first()
    if existing_phone:
       raise Conflict("Phone number already exists")

    
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    for role_id in role_ids:
        new_user_role = UserHasRole(user_id=new_user.user_id, role_id=role_id)
        db.session.add(new_user_role)
        db.session.commit()
    return BaseResponse.success("create success!")
 

@user_blueprint.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@has_permission('update')
def update_user(user_id):
    data = request.get_json()
    user_name = data.get('user_name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    role_ids = data.get('role_id')
    
    user = User.query.get(user_id)
    if not user:
        raise NotFound("User not found with provided user_id.")

    if not user_name or not email or not phone_number or not role_ids:
        raise BadRequest("Missing required fields")
    
    existing_email = User.query.filter(User.email == email, User.user_id != user_id).first()
    if existing_email:
        raise Conflict("Email already exists")
    
    existing_phone = User.query.filter(User.phone_number == phone_number, User.user_id != user_id).first()
    if existing_phone:
        raise Conflict("Phone number already exists")
    try:
        user.user_name = user_name  
        user.email = email   
        user.phone_number = phone_number   

        UserHasRole.query.filter_by(user_id=user_id).delete()
        for role_id in role_ids:
            new_user_role = UserHasRole(user_id=user_id, role_id=role_id)
            db.session.add(new_user_role)

        db.session.commit()
        return jsonify({'message': 'Updated user successfully'}),200
    except Exception as e:
        db.session.rollback()
        raise InternalServerError() from e
    
@user_blueprint.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@has_permission("delete")
def delete_user(user_id):
    user=User.query.get(user_id)
    if not user:
        raise NotFound("User not found with provided user_id.")
    try:
        booking_users = BookingUser.query.filter_by(user_id=user_id).all()
        for booking_user in booking_users:
            db.session.delete(booking_user)

        user_has_roles=UserHasRole.query.filter_by(user_id=user_id).all()
        for user_has_role in user_has_roles:
            db.session.delete(user_has_role)

        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Delete user successfully'}), 200
    except Exception as e:
        db.session.rollback()
        raise InternalServerError() from e