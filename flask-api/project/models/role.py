from project.models import db
from sqlalchemy.orm import validates  
from werkzeug.exceptions import BadRequest

class Role(db.Model):
    __tablename__ = "role"
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False)
    user_has_role = db.relationship('UserHasRole', backref='role')

    @validates('role_id')
    def validate_username(self, key, role_id):
        try:
            role_id = int(role_id) 
        except BadRequest:
            raise BadRequest("Invalid role_id format. Must be an integer.")
        return role_id 

    @validates('role_name')
    def validate_role_name(self, key, role_name):
        if len(role_name) > 50:
            raise BadRequest("Role name  exceeds maximum lengt")
        return role_name