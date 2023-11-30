from project.models.user import User
from project.models.user_has_role import UserHasRole
from project.models.role import Role
from project.models.role_has_permission import RoleHasPermission
from project.models.permission import Permission
from typing import Optional, Union, List
from project import db


class UserExecutor:

    @staticmethod
    def get_user_by_email(email: str):
        user = User.query.filter_by(email=email, is_deleted=0).first()
        return user

    @staticmethod
    def get_user(user_id: int):
        user = User.query.filter_by(user_id=user_id, is_deleted=0).first()
        return user

    @staticmethod
    def get_role_names(user_id: int):
        user = User.query.filter_by(user_id=user_id, is_deleted=0).first()
        role_names = [
            user_role.role.role_name for user_role in user.user_has_role]
        return role_names

    @staticmethod
    def get_permission_names(role_name: str):
        role = Role.query.filter_by(role_name=role_name).first()
        if role:
            role_permissions = (
                db.session.query(Permission.permission_name)
                .join(RoleHasPermission, Permission.permission_id == RoleHasPermission.permission_id)
                .filter(RoleHasPermission.role_id == role.role_id)
                .all()
            )
            permission_names = [rp[0] for rp in role_permissions]
            return permission_names
        return []
    # def get_permission_names_by_role_name(role_name: str):
    #     role = Role.query.filter_by(role_name=role_name).first()
    #     if role:
    #         permissions = [
    #             role_has_permission.permission.permission_name
    #             for role_has_permission in role.role_has_permission
    #         ]
    #         return permissions
    #     return []

    @staticmethod
    def get_list_users(page: int, per_page: int):
        users = User.query.filter_by(is_deleted=False).paginate(
            page=page, per_page=per_page, error_out=False)

        return users

    @staticmethod
    def add_user(new_user: object):
        db.session.add(new_user)
        db.session.commit()

    @staticmethod
    def search_list_user(page: int, per_page: int, search: str) : 
        users = User.query.filter(User.is_deleted == False).filter(
            (User.email.like(f'%{search}%')) |
            (User.user_name.like(f'%{search}%'))
        ).paginate(page=page, per_page=per_page, error_out=False)
        return users