from project.models import db

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