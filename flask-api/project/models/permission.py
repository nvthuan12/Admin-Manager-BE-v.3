from project.models import db
from sqlalchemy.orm import validates  
from werkzeug.exceptions import BadRequest

class Permission(db.Model):
    __tablename__ = "permission"
    permission_id = db.Column(db.Integer, primary_key=True)
    permission_name = db.Column(db.String(80), nullable=False)
    role_has_permission = db.relationship('RoleHasPermission', backref='permission')

    @validates('permission_id')
    def validate_username(self, key, permission_id):
        try:
            permission_id = int(permission_id) 
        except BadRequest:
            raise BadRequest("Invalid permission_id format. Must be an integer.")
        return permission_id 

    @validates('permission_name')
    def validate_permission_name(self, key, permission_name):
        if len(permission_name) > 80:
            raise BadRequest("Permission name exceeds maximum length.")
        return permission_name