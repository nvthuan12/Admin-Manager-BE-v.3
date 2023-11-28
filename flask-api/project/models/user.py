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
            'phone_number': self.phone_number
        }
    
    @validates('user_id')
    def validate_username(self, key, user_id):
        try:
            user_id = int(user_id) 
        except BadRequest:
            raise BadRequest("Invalid user_id format. Must be an integer.")
        return user_id 
    
    @validates('user_name')
    def validate_user_name(self, key, user_name):
        if len(user_name) > 80:
            raise BadRequest("User name exceeds maximum length")
        return user_name
    
    @validates('email') 
    def validate_email(self, key, email):
        if len(email) > 50:
            raise BadRequest("User name exceeds maximum length")
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise BadRequest("Invalid email format") 
        return email
    
    @validates('phone_number') 
    def validate_phone_number(self, key, phone_number):
        if len(phone_number) > 11:
            raise BadRequest('Phone number exceeds maximum length')
        if not re.match(r'^0\d{9}$' , phone_number):
            raise BadRequest('Invalid phone number format') 
        return phone_number
    

    