from project.models import Booking, BookingUser, Room
from typing import List, Optional, Union
from project import db

class UserBookingExecutor:
    @staticmethod
    def check_room_availability(room_id: int, time_start: str, time_end: str) -> Optional[Booking]:
        return Booking.query.filter(
            Booking.room_id == room_id,
            Booking.time_end >= time_start,
            Booking.time_start <= time_end
        ).first()
    
    @staticmethod
    def get_bookings_in_date_range_user(start_date, end_date, user_id) -> List[Booking]:
        return Booking.query.filter(
            BookingUser.user_id == user_id,
            Booking.is_deleted == False,
            Booking.time_end.between(start_date, end_date)
        ).all()
    
    @staticmethod
    def create_booking_belong_to_user(room_id: int, title: str, time_start: str, time_end: str, user_ids: List[int]) -> Booking:
        try:
            new_booking = Booking(
                room_id=room_id, title=title, time_start=time_start, time_end=time_end, is_accepted=False, is_deleted=False)
            db.session.add(new_booking)
            db.session.commit()

            for user_id in user_ids:
                user_booking = BookingUser(
                    user_id=user_id, booking_id=new_booking.booking_id, is_attending=False)
                db.session.add(user_booking)
            db.session.commit()

            return new_booking
        except Exception as e:
            db.session.rollback()
            raise e