import re
from project.models import db
from flask_bcrypt import bcrypt
from sqlalchemy.orm import validates  
from werkzeug.exceptions import BadRequest  

class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    phone_number = db.Column(db.String(11), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False)
    updated_at = db.Column(db.TIMESTAMP, nullable=False)
    is_deleted= db.Column(db.Boolean, nullable=False)
    booking_user = db.relationship('BookingUser', backref='user')
    user_has_role = db.relationship('UserHasRole', backref='user')
    
    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def serialize(self):
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'email': self.email,
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat(),  # Chuyển đổi sang chuẩn ISO 8601 cho datetime
            'updated_at': self.updated_at.isoformat(),
            'is_deleted': self.is_deleted,
            'bookings': [booking.serialize() for booking in self.booking_user],
            'roles': [role.serialize() for role in self.user_has_role]
        }

    @staticmethod
    def validate_user_name(user_name):
        if not user_name.strip():
            return {"field": "user_name", "message":"User name cannot be empty or contain only whitespace"}
        elif len(user_name) > 50:
            return {"field": "user_name", "message":"User name exceeds maximum length"}
        return None

    @staticmethod
    def validate_email(email):
        if not email.strip():   
            return {"field": "email", "message": "Email cannot be empty or contain only whitespace"}
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return {"field": "email","message": "Format email must be: example@example.com)"}
        return None
    @staticmethod
    def validate_phone_number(phone_number):
        if not phone_number.strip():
            return {"field": "phone_number","message":"Phone number cannot be empty or contain only whitespace"}
        elif not re.match(r'^0\d{9}$' , phone_number):
            return {"field": "phone_number","message":"Phone number must be have 10 number and format: 0*********"}
        return None

    @staticmethod
    def validate_password(password):
        if not password.strip():
            return {"field": "password","message":"Password cannot be empty or contain only whitespace"}
        elif not re.match(r'^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d]{8,}$' , password):
            return {"field": "password","message":"Password must be at least 8 characters, at least one letter and at least one number"}
        return None

    def validate_all_fields(self):
        errors = []
        errors.append(self.validate_user_name(self.user_name))
        errors.append(self.validate_email(self.email))
        errors.append(self.validate_phone_number(self.phone_number))
        errors.append(self.validate_password(self.password))
        
        errors = [error for error in errors if error is not None]
        return errors
    