from project.database.excute.user import get_user_by_email
from datetime import timedelta
from flask import jsonify
from flask_jwt_extended import create_access_token
from project.api.v1.has_permission import get_role_names  

class AuthService:
    @staticmethod
    def authenticate_user(email, password):
        user = get_user_by_email(email)
        if not user or not user.check_password(password):
            return None
        return user

    @staticmethod
    def login_user(user):
        access_token = create_access_token(identity=user.user_id, expires_delta=timedelta(days=1))
        role_name = get_role_names(user.user_id)
        data= access_token=access_token
        return data
    
