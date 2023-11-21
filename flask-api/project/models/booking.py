from project.models import db
from sqlalchemy.orm import validates  
from werkzeug.exceptions import BadRequest
from datetime import datetime

class Booking(db.Model):
    __tablename__ = "booking"
    booking_id = db.Column(db.Integer, primary_key=True)
    time_start = db.Column(db.TIMESTAMP, nullable=False)
    time_end = db.Column(db.TIMESTAMP, nullable=False)
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

    # @validates('time_start')
    # def validate_time_start(self, key, time_start):

    #     if time_start < datetime.datetime.utcnow():
    #         raise BadRequest("must be in the future")
    #     if time_start <= self.time_end:
    #         print("1")
    #         raise BadRequest("time_start must be greater than time_end")
    #     return time_start

    # @validates('time_end')
    # def validate_time_end(self, key, time_end):
    #     if time_end <= datetime.datetime.utcnow():
    #         print("2")
    #         raise BadRequest("time_end must be in the future")
    #     return time_end