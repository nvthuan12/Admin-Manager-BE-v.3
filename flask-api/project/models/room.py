from project.models import db
from sqlalchemy.orm import validates  
from werkzeug.exceptions import BadRequest

class Room(db.Model):
    __tablename__ = "room"
    room_id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.Boolean, nullable=False)
    booking = db.relationship('Booking', backref='room')

    def serialize(self):
        return {
            'room_id': self.room_id,
            'room_name': self.room_name,
            'status': self.status,
        }

    @validates('room_id')
    def validate_username(self, key, room_id):
        try:
            room_id = int(room_id) 
        except BadRequest:
            raise BadRequest("Invalid room_id format. Must be an integer.")
        return room_id     

    @validates('room_name')
    def validate_room_name(self, key, room_name):
        if len(room_name) > 80:
            raise BadRequest('Room name exceeds maximum length')
        return room_name

    @validates('status')
    def validate_status(self, key, status):
        if status not in [True, False]:
            raise BadRequest('Invalid status value, must be True or False')
        return status