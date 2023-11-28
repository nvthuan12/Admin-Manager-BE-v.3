from project.models import db

class BookingUser(db.Model):
    __tablename__ = "booking_user"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id'))
    is_attending = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    def serialize(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'user_id': self.user_id
        }