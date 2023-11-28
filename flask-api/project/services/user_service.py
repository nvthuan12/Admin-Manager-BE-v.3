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
from project.database.excute.user import get_paginated_users

class UserService:

    @staticmethod
    def get_paginated_users(page, per_page):
        users=get_paginated_users(page,per_page)
        total_pages = users.pages
        total_items = users.total
        
        paginated_users = []
        for user in users.items:
            paginated_users.append({
                "user_id": user.user_id,
                "user_name": user.user_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "role_id": user.role_id,
                "role_name": user.role_name,
                "is_deleted": user.is_deleted
            })
        
        result = {
            'total_pages': total_pages,
            'total_items': total_items,
            'current_page': page,
            "list_users": paginated_users
        }
        return result
    
    