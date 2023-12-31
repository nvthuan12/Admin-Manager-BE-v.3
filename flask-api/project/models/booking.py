from project.models import db
from sqlalchemy.orm import validates
from werkzeug.exceptions import BadRequest
from datetime import datetime

class Booking(db.Model):
    __tablename__ = "booking"
    booking_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    time_start = db.Column(db.TIMESTAMP, nullable=False)
    time_end = db.Column(db.TIMESTAMP, nullable=False)
    is_accepted = db.Column(db.Boolean, nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False)
    deleted_at = db.Column(db.TIMESTAMP, nullable=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'))
    creator_id=db.Column(db.Integer, db.ForeignKey('user.user_id'))
    booking_user = db.relationship('BookingUser', backref='booking')

    def serialize(self):
        return {
            'booking_id': self.booking_id,
            'title': self.title,
            'time_start': self.time_start.strftime('%Y-%m-%d %H:%M:%S'),
            'time_end': self.time_end.strftime('%Y-%m-%d %H:%M:%S'),
            'is_accepted': self.is_accepted,
            'is_deleted': self.is_deleted,
            'room_id': self.room_id,
            'creator_id': self.creator_id,
            'booking_user': [be.serialize() for be in self.booking_user],
            'deleted_at': self.deleted_at
        }

    @staticmethod
    def validate_title(title: str) -> dict[str, str] | None:
        if not title.strip():
            return {"field": "title", "error": "Title cannot be empty or contain only whitespace"}
        elif len(title) > 255:
            return {"field": "title", "error": "Title exceeds maximum length"}
        return None

    @staticmethod
    def validate_time(time_start: str, time_end: str) -> dict[str, str] | None:
        current_time = str(datetime.now())
        if time_start >= time_end:
            return {"field": "time_end", "error": "Time end must be after time start"}
        elif time_start < current_time or time_end < current_time:
            return {"field": "time_start", "error": "Cannot select time in the past"}
        return None

    def validate_all_fields(self):
        errors = []
        errors.append(self.validate_title(self.title))
        errors.append(self.validate_time(self.time_start, self.time_end))

        errors = [error for error in errors if error is not None]
        return errors
