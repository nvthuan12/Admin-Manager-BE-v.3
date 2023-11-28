from project.models import db
from sqlalchemy.orm import validates  
from werkzeug.exceptions import BadRequest
from datetime import datetime

class Booking(db.Model):
    __tablename__ = "booking"
    booking_id = db.Column(db.Integer, primary_key=True)
    title=  db.Column(db.String(255), nullable=False)
    time_start = db.Column(db.TIMESTAMP, nullable=False)
    time_end = db.Column(db.TIMESTAMP, nullable=False)
    is_accepted= db.Column(db.Boolean, nullable=False)
    is_deleted= db.Column(db.Boolean, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'))
    booking_user = db.relationship('BookingUser', backref='booking')
    
    def serialize(self):
        return {
            'booking_id': self.booking_id,
            'time_start': self.time_start.strftime('%Y-%m-%d %H:%M:%S'),
            'time_end': self.time_end.strftime('%Y-%m-%d %H:%M:%S'),
            'room_id': self.room_id,
            'booking_user': [be.serialize() for be in self.booking_user]
        }
    
    @validates('booking_id')
    def validate_username(self, key, booking_id):
        try:
            booking_id = int(booking_id) 
        except BadRequest:
            raise BadRequest("Invalid booking_id format. Must be an integer.")
        return booking_id 

    @validates('title')
    def validate_title(self, key, title):
        if len(title) > 255:
            raise BadRequest("Title exceeds maximum length.")
        return title