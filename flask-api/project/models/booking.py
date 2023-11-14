from project.models import db

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