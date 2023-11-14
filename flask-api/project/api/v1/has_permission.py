from functools import wraps
from flask import request, jsonify
from project import db
from project.models.user import User 
from project.models.role import Role 
from project.models.user_has_role import UserHasRole 
from project.models.permission import Permission 
from project.models.role_has_permission import RoleHasPermission 
from flask_jwt_extended import JWTManager,get_jwt_identity
import project.api.common.utils.exceptions as exceptions
from collections import defaultdict

# Hàm để lấy vai trò của người dùng dựa trên employee_id
def get_role_names(user_logged_id):
    role_names = (db.session.query(Role.role_name).
        join(UserHasRole, Role.role_id == UserHasRole.role_id).
        join(User, User.user_id == UserHasRole.user_id).
        filter(User.user_id == user_logged_id).all()
    )
    return [role_name[0] for role_name in role_names]
   
def get_permission_name(role_name):
    permission_names = (
    db.session.query(Permission.permission_name)
    .join(RoleHasPermission, Permission.permission_id == RoleHasPermission.permission_id)
    .join(Role, RoleHasPermission.role_id == Role.role_id)
    .filter(Role.role_name == role_name)
    .all()
    )
    return [permission_name[0] for permission_name in permission_names]

# Hàm kiểm tra quyền truy cập
def has_permission(required_permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_logged_id = get_jwt_identity()
            print("id",user_logged_id)
            if not user_logged_id:
                return exceptions.UNAUTHORIZED_401
            
            role_names = get_role_names(user_logged_id)
            print("permission:",role_names)
            list_perssion_name=[]

            for role_name in role_names:
                print("permission:",role_name)
                actions = get_permission_name(role_name)
                for action in actions:
                    if action not in list_perssion_name:
                        list_perssion_name.append(action)
                
            print("permission:",list_perssion_name)
            for action in list_perssion_name:
                if required_permission == action:
                    return func(*args, **kwargs)
                else:
                    return exceptions.ACCESS_DENIED_403
        return wrapper
    return decorator
