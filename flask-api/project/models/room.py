from project.models import db
from sqlalchemy.orm import validates  
from werkzeug.exceptions import BadRequest

class Room(db.Model):
    __tablename__ = "room"
    room_id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_blocked = db.Column(db.Boolean, nullable=False)
    deleted_at = db.Column(db.TIMESTAMP, nullable=True)
    booking = db.relationship('Booking', backref='room')

    def serialize(self):
        return {
            'room_id': self.room_id,
            'room_name': self.room_name,
            'description': self.description,
            'is_blocked': self.is_blocked,
            'deleted_at': self.deleted_at
        }

    @validates('room_id')
    def validate_room_id(self, key, room_id):
        try:
            room_id = int(room_id)
        except ValueError:
            raise BadRequest("Invalid room_id format. Must be an integer.")
        return room_id     

    @validates('room_name')
    def validate_room_name(self, key, room_name):
        if not room_name or room_name.isspace():
            raise BadRequest("Room name cannot be empty.")
        if len(room_name) > 50:
            raise BadRequest("Room name exceeds maximum length")
        return room_name

    @validates('description')
    def validate_description(self, key, description):
        if description is None or description.isspace():
            raise BadRequest("Description is required.")
        return description

    @validates('is_blocked')
    def validate_is_blocked(self, key, is_blocked):
        if is_blocked not in [True, False]:
            raise BadRequest("Invalid is_blocked value, must be True or False")
        return is_blocked