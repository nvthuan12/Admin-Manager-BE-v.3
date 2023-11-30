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
    @staticmethod
    def validate_room_name(room_name: str) -> dict[str,str] | None:
        if not room_name.strip():
            return {"field": "room_name", "error": "Room name cannot be empty or contain only whitespace"}
        elif len(room_name) > 50:
            return {"field": "room_name", "error": "Room name exceeds maximum length"}
        return None

    @staticmethod
    def validate_description(description: str) -> dict[str,str] | None:
        if not description.strip():
            return {"field": "description", "error": "Description cannot be empty or contain only whitespace"}
        elif len(description) > 255:
            return {"field": "description", "error": "Description exceeds maximum length (255 characters)"}
        return None
    
    def validate_all_fields(self):
        errors = []
        errors.append(self.validate_room_name(self.room_name))
        errors.append(self.validate_description(self.description))

        errors = [error for error in errors if error is not None]
        return errors
