from project.database.excute.booking import BookingExecutor
from project.models import Room, Booking, BookingUser, User
from project.api.common.base_response import BaseResponse
from werkzeug.exceptions import BadRequest, InternalServerError, Conflict, NotFound
from flask import request
from datetime import datetime, timedelta
from typing import List
from project.database.excute.room import RoomExecutor
from typing import Union, Dict, Optional, List
from flask_jwt_extended import get_jwt_identity

class BookingService:
    @staticmethod
    def get_bookings_in_date_range() -> dict:
        start_date_str = request.args.get('start_date', None)
        end_date_str = request.args.get('end_date', None)

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        else:
            raise BadRequest("Both start_date and end_date are required for date range query.")

        bookings = BookingExecutor.get_bookings_in_date_range(start_date, end_date)

        list_bookings = []
        for booking in bookings:
            user_names = [
                booking_user.user.user_name for booking_user in booking.booking_user]
            user_ids =  [booking_user.user_id for booking_user in booking.booking_user]
            room = Room.query.filter_by(room_id=booking.room_id).first()
            room_name = room.room_name if room else None
            booking_info = {
                "booking_id": booking.booking_id,
                "title": booking.title,
                "time_start": booking.time_start.strftime('%Y-%m-%d %H:%M:%S'),
                "time_end": booking.time_end.strftime('%Y-%m-%d %H:%M:%S'),
                "room_name": room_name,
                "user_name": user_names,
                "room_id": booking.room_id,
                "user_id": user_ids,
                "is_accepted": booking.is_accepted
            }
            list_bookings.append(booking_info)

        return list_bookings


    @staticmethod
    def book_room(data:  Dict) :
        room_id = data.get('room_id')
        title = data.get('title')
        time_start= data.get('time_start')
        time_end= data.get('time_end')
        user_ids = data.get('user_id', [])

        errors = []
        validate_title = Booking.validate_title(title)
        if validate_title:
            errors.append(validate_title)

        validate_time = Booking.validate_time(time_start, time_end)
        if validate_time:
            errors.append(validate_time)
        if errors:
            return BaseResponse.error_validate(errors)

        existing_booking: Optional[Booking] = BookingExecutor.check_room_availability(room_id, time_start, time_end)

        if existing_booking:
            raise Conflict('Room is already booked for this time')
        else:
            new_booking = BookingExecutor.create_booking(room_id, title, time_start, time_end, user_ids)
        return BaseResponse.success( 'Booking created successfully')
    
    @staticmethod
    def update_booking(booking_id: int, data: Dict) -> Union[Dict, None]:
            room_id: int = data.get('room_id')
            title: str = data.get('title')
            time_start: str = data.get('time_start') 
            time_end: str = data.get('time_end')
            user_ids: List[int] = data.get('user_id', [])

            booking = BookingExecutor.get_booking(booking_id)

            if not booking:
                raise NotFound('Booking not found')
            
            errors = []
            validate_title = Booking.validate_title(title)
            if validate_title:
                errors.append(validate_title)

            validate_time = Booking.validate_time(time_start, time_end)
            if validate_time:
                errors.append(validate_time)

            if errors:
                return BaseResponse.error_validate(errors)

            existing_booking = BookingExecutor.check_room_availability_update(room_id, time_start, time_end, booking_id)

            if existing_booking:
                raise Conflict('Room is already booked for this time')

            BookingExecutor.update_booking(booking, room_id, title, time_start, time_end, user_ids,)

            return BaseResponse.success( 'Booking updated successfully')
    
    @staticmethod
    def delete_booking_service(booking_id: int) -> Dict:
        booking = Booking.query.get(booking_id)

        if not booking:
            raise NotFound('Booking not found')

        if booking.is_deleted:
            raise BadRequest('Booking is already deleted')

        room_status = BookingExecutor.is_room_blocked(booking.room_id)

        if room_status:
            raise BadRequest('Cannot delete the booking, the room is currently in use')

        booking.is_deleted = True
        booking.deleted_at = datetime.now()

        BookingExecutor.commit()
        return BaseResponse.success( 'Booking deleted successfully')
    
    @staticmethod
    def search_booking_users(start_date: str, end_date: str ,user_ids: List[int] ) -> List[Booking]:
        bookings = BookingExecutor.search_booking_users(start_date, end_date, user_ids)
        list_bookings = []
        for booking in bookings:
            user_ids = [booking_user.user.user_id for booking_user in booking.booking_user]
            user_names = [booking_user.user.user_name for booking_user in booking.booking_user]
            room = Room.query.filter_by(room_id=booking.room_id).first()
            room_name = room.room_name if room else None
            booking_info = {
                "booking_id": booking.booking_id,
                "title": booking.title,
                "time_start": booking.time_start.strftime('%Y-%m-%d %H:%M:%S'),
                "time_end": booking.time_end.strftime('%Y-%m-%d %H:%M:%S'),
                "room_name": room_name,
                "user_ids": user_ids,  
                "user_names": user_names
            }
            list_bookings.append(booking_info)
        return list_bookings
    
    @staticmethod
    def search_booking_room(start_date:str , end_date:str,room_id: int ) -> List[Booking]:
        bookings = BookingExecutor.search_booking_room(start_date, end_date, room_id)
        list_bookings = []
        for booking in bookings:
            user_ids = [booking_user.user.user_id for booking_user in booking.booking_user]
            user_names = [booking_user.user.user_name for booking_user in booking.booking_user]
            room = Room.query.filter_by(room_id=booking.room_id).first()
            room_name = room.room_name if room else None
            booking_info = {
                "booking_id": booking.booking_id,
                "title": booking.title,
                "time_start": booking.time_start.strftime('%Y-%m-%d %H:%M:%S'),
                "time_end": booking.time_end.strftime('%Y-%m-%d %H:%M:%S'),
                "room_name": room_name,
                "user_ids": user_ids,  
                "user_names": user_names
            }
            list_bookings.append(booking_info)
        return list_bookings
    
    @staticmethod
    def get_bookings_in_date_range_user() -> dict:
        user_id = get_jwt_identity()
        start_date_str = request.args.get('start_date', None)
        end_date_str = request.args.get('end_date', None)
        creator_id = user_id

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        else:
            raise BadRequest("Both start_date and end_date are required for date range query.")

        bookings = BookingExecutor.get_bookings_in_date_range_user(start_date, end_date, user_id)
        list_bookings = []
        for booking in bookings:
            user_ids = [booking_user.user_id for booking_user in booking.booking_user]
            if user_id in user_ids:        
                user_names = [
                    booking_user.user.user_name for booking_user in booking.booking_user]
                user_ids =  [booking_user.user_id for booking_user in booking.booking_user]
                room = Room.query.filter_by(room_id=booking.room_id).first()
                room_name = room.room_name if room else None
                booking_info = {
                    "booking_id": booking.booking_id,
                    "title": booking.title,
                    "time_start": booking.time_start.strftime('%Y-%m-%d %H:%M:%S'),
                    "time_end": booking.time_end.strftime('%Y-%m-%d %H:%M:%S'),
                    "room_name": room_name,
                    "user_name": user_names,
                    "room_id": booking.room_id,
                    "user_id": user_ids,
                    "is_accepted": booking.is_accepted,
                    "creator_id": booking.creator_id
                }
                list_bookings.append(booking_info)

        return list_bookings
    
    @staticmethod
    def book_room_belong_to_user(data:  Dict) :
        room_id = data.get('room_id')
        title = data.get('title')
        time_start= data.get('time_start')
        time_end= data.get('time_end')
        user_ids = data.get('user_id', [])

        errors = []
        validate_title = Booking.validate_title(title)
        if validate_title:
            errors.append(validate_title)

        validate_time = Booking.validate_time(time_start, time_end)
        if validate_time:
            errors.append(validate_time)
        if errors:
            return BaseResponse.error_validate(errors)

        existing_booking: Optional[Booking] = BookingExecutor.check_room_availability(room_id, time_start, time_end)

        if existing_booking:
            raise Conflict('Room is already booked for this time')
        else:
            new_booking = BookingExecutor.create_booking_belong_to_user(room_id, title, time_start, time_end, user_ids)
        return BaseResponse.success( 'Booking created successfully')
    
    