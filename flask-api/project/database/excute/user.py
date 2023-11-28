from project.models.user import User
from project.models.user_has_role import UserHasRole
from project.models.role import Role
from project import db

def get_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    return user

def get_paginated_users(page, per_page):
    users = User.query.join(UserHasRole).join(Role).with_entities(
        User.user_id,
        User.user_name,
        User.email,
        User.phone_number,
        User.is_deleted,
        UserHasRole.role_id,
        Role.role_name,
    ).paginate(page=page, per_page=per_page, error_out=False)
    return users