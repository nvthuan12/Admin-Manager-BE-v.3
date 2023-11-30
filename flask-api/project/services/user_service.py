from flask import Blueprint, request, jsonify
from project import app, db
from werkzeug.exceptions import Conflict, InternalServerError, NotFound
from project.models.user import User
from project.models.user_has_role import UserHasRole
from project.models.user_has_role import UserHasRole
from project.api.common.base_response import BaseResponse
from project.database.excute.user import UserExecutor
from typing import Dict, List
from math import ceil
from datetime import datetime


class UserService:

    @staticmethod
    def paginated_users(users:  List[User]):
        paginated_users = []
        for user in users.items:
            roles = [user_role.role.role_name for user_role in user.user_has_role]
            user_info = {
                "user_id": user.user_id,
                "user_name": user.user_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": user.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "role_name": roles
            }
            paginated_users.append(user_info)
        return paginated_users

    @staticmethod
    def get_list_users(page: int, per_page: int):
        users = UserExecutor.get_list_users(page, per_page)
        paginated_users = UserService.paginated_users(users)

        total_items = users.total
        total_pages = ceil(total_items / per_page)
        per_page = per_page
        current_page = page
        result = {
            'users': paginated_users,
            'total_items': total_items,
            'per_page': per_page,
            'current_page': current_page,
            'total_pages': total_pages
        }
        return result

    @staticmethod
    def add_new_user(data: Dict):
        user_name = data.get('user_name')
        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data.get('password')
        role_ids = data.get('role_id')
        created_at = datetime.now()
        updated_at = datetime.now()
        is_deleted = False
        new_user = User(
            user_name=user_name,
            email=email,
            phone_number=phone_number,
            password=password,
            created_at=created_at,
            updated_at=updated_at,
            is_deleted=is_deleted
        )
        validate_error = new_user.validate_all_fields()
        if validate_error:
            return BaseResponse.error_validate(validate_error)

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            raise Conflict("Email already exists")

        existing_phone = User.query.filter_by(
            phone_number=phone_number).first()
        if existing_phone:
            raise Conflict("Phone number already exists")

        new_user.set_password(password)
        UserExecutor.add_user(new_user)

        for role_id in role_ids:
            new_user_role = UserHasRole(
                user_id=new_user.user_id, role_id=role_id)
            db.session.add(new_user_role)
            db.session.commit()
        return BaseResponse.success("User created successfully")

    @staticmethod
    def update_user(data: Dict, user_id: int):
        user_name = data.get('user_name')
        phone_number = data.get('phone_number')
        role_ids = data.get('role_id')
        user = UserExecutor.get_user(user_id)

        if not user:
            raise NotFound("User not found with provided user_id.")

        errors = []
        validate_phone_number = User.validate_phone_number(phone_number)
        if validate_phone_number:
            errors.append(validate_phone_number)

        validate_user_name = User.validate_user_name(user_name)
        if validate_user_name:
            errors.append(validate_user_name)
        if errors:
            return BaseResponse.error_validate(errors)

        existing_phone = User.query.filter(
            User.phone_number == phone_number, User.user_id != user_id).first()
        if existing_phone:
            raise Conflict("Phone number already exists")

        user.user_name = user_name
        user.phone_number = phone_number
        user.updated_at = datetime.now()
        UserHasRole.query.filter_by(user_id=user_id).delete()
        for role_id in role_ids:
            new_user_role = UserHasRole(user_id=user_id, role_id=role_id)
            db.session.add(new_user_role)
        db.session.commit()
        return BaseResponse.success("Updated user successfully")

    @staticmethod
    def delete_user(user_id: int):
        user = UserExecutor.get_user(user_id)
        if not user:
            raise NotFound("User not found with provided user_id.")
        user.is_deleted = True
        user.updated_at = datetime.now()
        db.session.commit()
        return BaseResponse.success("Deleted success!")

    @staticmethod
    def search_list_user(page: int, per_page: int, search: str):
        users = UserExecutor.search_list_user(page, per_page, search)
        if users is None:
            raise NotFound("No data found")

        paginated_users = UserService.paginated_users(users)

        total_items = users.total
        total_pages = ceil(total_items / per_page)
        per_page = per_page
        current_page = page
        result = {
            'users': paginated_users,
            'total_items': total_items,
            'per_page': per_page,
            'current_page': current_page,
            'total_pages': total_pages
        }
        return BaseResponse.success(result)
