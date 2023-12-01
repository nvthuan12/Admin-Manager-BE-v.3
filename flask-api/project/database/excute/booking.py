from project.models import Booking, BookingUser, Room
from typing import List, Optional, Union
from project import db


class BookingExecutor:
    @staticmethod
    def get_bookings_in_date_range(start_date, end_date) -> List[Booking]:
        return Booking.query.filter(
            Booking.is_deleted == False,
            Booking.time_end.between(start_date, end_date)
        ).all()
    
    @staticmethod
    def check_room_availability(room_id: int, time_start: str, time_end: str) -> Optional[Booking]:
        return Booking.query.filter(
            Booking.room_id == room_id,
            Booking.time_end >= time_start,
            Booking.time_start <= time_end
        ).first()
    
    @staticmethod
    def check_room_availability_update(room_id: int, time_start: str, time_end: str, booking_id: int) -> Optional[Booking]:
        return Booking.query.filter(
            Booking.room_id == room_id,
            Booking.time_end >= time_start,
            Booking.time_start <= time_end,
            Booking.booking_id != booking_id
        ).first()

    @staticmethod
    def create_booking(room_id: int, title: str, time_start: str, time_end: str, user_ids: List[int]) -> Booking:
        try:
            new_booking = Booking(
                room_id=room_id, title=title, time_start=time_start, time_end=time_end, is_accepted=True, is_deleted=False)
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
        
    @staticmethod
    def get_booking(booking_id: int) -> Optional[Booking]:
        return Booking.query.get(booking_id)
    
    @staticmethod
    def db_commit(booking_id: int) -> Optional[Booking]:
        return Booking.query.get(booking_id)

    @staticmethod
    def update_booking(booking: Booking, room_id: int, title: str, time_start: str, time_end: str, user_ids: List[int]) -> None:
        try:
            booking.room_id = room_id
            booking.title = title
            booking.time_start = time_start
            booking.time_end = time_end

            BookingUser.query.filter_by(booking_id=booking.booking_id).delete()

            for user_id in user_ids:
                user_booking = BookingUser(
                    user_id=user_id, booking_id=booking.booking_id, is_attending=False)
                db.session.add(user_booking)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        
    @staticmethod
    def is_room_blocked(room_id: int) -> Union[bool, None]:
        return Room.query.filter_by(room_id=room_id).value(Room.is_blocked)
    
    @staticmethod
    def commit():
        db.session.commit()
