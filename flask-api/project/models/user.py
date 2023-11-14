from project.models import db
from flask_bcrypt import bcrypt

class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(11), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
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