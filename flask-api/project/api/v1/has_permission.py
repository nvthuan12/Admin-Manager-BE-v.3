from functools import wraps
from project import db
from project.models.user import User 
from project.models.role import Role 
from project.models.user_has_role import UserHasRole 
from project.models.permission import Permission 
from project.models.role_has_permission import RoleHasPermission 
from flask_jwt_extended import get_jwt_identity
from werkzeug.exceptions import Unauthorized, Forbidden

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

def has_permission(required_permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_logged_id = get_jwt_identity()
            if not user_logged_id:
                raise Unauthorized()
    
            role_names = get_role_names(user_logged_id)
            list_perssion_name=[]
            for role_name in role_names:
                permissions = get_permission_name(role_name)
                for permission in permissions:
                    if permission not in list_perssion_name:
                        list_perssion_name.append(permission)
     
            if required_permission in list_perssion_name:
                return func(*args, **kwargs)
            else:
                raise Forbidden()
        return wrapper
    return decorator
