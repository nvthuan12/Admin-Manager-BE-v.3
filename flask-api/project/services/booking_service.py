from project.database.excute.booking import BookingExecutor
from project.models import Room, Booking, BookingUser, User
from project.api.common.base_response import BaseResponse
from werkzeug.exceptions import BadRequest, InternalServerError, Conflict, NotFound
from flask import request
from datetime import datetime, timedelta
from typing import List
from project.database.excute.room import RoomExecutor
from typing import Union, Dict, Optional, List
from math import ceil
from flask_jwt_extended import get_jwt_identity
from project import db

class BookingService:

    @staticmethod
    def show_list_booking(bookings: List[Booking]):
        list_bookings = []
        for booking in bookings:
            user_ids = [booking_user.user.user_id for booking_user in booking.booking_user]
            user_names = [booking_user.user.user_name for booking_user in booking.booking_user]
            booking_users = [booking_user.serialize() for booking_user in booking.booking_user]
            user_created= User.query.filter_by(user_id=booking.creator_id).first()
            creator_name=user_created.user_name if user_created else None
            room = Room.query.filter_by(room_id=booking.room_id).first()
            room_name = room.room_name if room else None
            
            booking_info = {
                "booking_id": booking.booking_id,
                "title": booking.title,
                "time_start": booking.time_start.strftime('%Y-%m-%d %H:%M:%S'),
                "time_end": booking.time_end.strftime('%Y-%m-%d %H:%M:%S'),
                "room_id": booking.room_id,
                "room_name": room_name,
                "user_ids": user_ids,  
                "user_names": user_names,
                "creator_id": booking.creator_id,
                "creator_name": creator_name,
                "is_accepted":booking.is_accepted,
                "is_deleted":booking.is_deleted,
                "booking_users":booking_users
            }
            list_bookings.append(booking_info) 
        return list_bookings

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

        list_bookings = BookingService.show_list_booking(bookings)
        return list_bookings

    @staticmethod
    def book_room(data:  Dict) :
        room_id = data.get('room_id')
        title = data.get('title')
        time_start= data.get('time_start')
        time_end= data.get('time_end')
        user_ids = data.get('user_ids', [])

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
            user_ids: List[int] = data.get('user_ids', [])

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
        list_bookings = BookingService.show_list_booking(bookings)
        return list_bookings
    
    @staticmethod
    def search_booking_room(room_id: int ) -> List[Booking]:

        start_date_str = request.args.get('start_date', None)
        end_date_str = request.args.get('end_date', None)

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        else:
            raise BadRequest("Both start_date and end_date are required for date range query.")
       
        bookings = BookingExecutor.search_booking_room(start_date, end_date, room_id)
        list_bookings = BookingService.show_list_booking(bookings)
        return list_bookings
    
    @staticmethod
    def get_bookings_in_date_range_user() -> dict:
        user_id = get_jwt_identity()
        start_date_str = request.args.get('start_date', None)
        end_date_str = request.args.get('end_date', None)

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        else:
            raise BadRequest("Both start_date and end_date are required for date range query.")

        bookings = BookingExecutor.get_bookings_in_date_range_user(start_date, end_date, user_id)
        list_bookings = BookingService.show_list_booking(bookings)
        return list_bookings
    
    @staticmethod
    def book_room_belong_to_user(data:  Dict) :
        room_id = data.get('room_id')
        title = data.get('title')
        time_start= data.get('time_start')
        time_end= data.get('time_end')
        user_ids = data.get('user_ids', [])

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
        return BaseResponse.success('Booking created successfully')

    @staticmethod
    def user_view_list_booked(page: int, per_page: int) -> List[Booking]:
        creator_id=get_jwt_identity()
        bookings=BookingExecutor.user_view_list_booked(page, per_page, creator_id)
        list_bookings = BookingService.show_list_booking(bookings)   
        total_items = bookings.total
        total_pages = ceil(total_items / per_page)
        per_page = per_page
        current_page = page
        result = {
            'list_bookings': list_bookings,
            'total_items': total_items,
            'per_page': per_page,
            'current_page': current_page,
            'total_pages': total_pages
        }
        return result
    
    @staticmethod
    def admin_view_booking_pending(page: int, per_page: int) -> List[Booking]:
        bookings=BookingExecutor.admin_view_booking_pending(page, per_page)
        list_bookings=BookingService.show_list_booking(bookings)  
        total_items = bookings.total
        total_pages = ceil(total_items / per_page)
        per_page = per_page
        current_page = page
        result = {
            'list_bookings': list_bookings,
            'total_items': total_items,
            'per_page': per_page,
            'current_page': current_page,
            'total_pages': total_pages
        }
        return result
    
    @staticmethod
    def detail_booking(booking_id: int):
        booking=BookingExecutor.get_booking(booking_id)
        if not booking:
            raise NotFound('Booking not found')
        user_ids = [booking_user.user.user_id for booking_user in booking.booking_user]
        user_names = [booking_user.user.user_name for booking_user in booking.booking_user]

        user_created = User.query.filter_by(user_id=booking.creator_id).first()
        creator_name = user_created.user_name if user_created else None

        room = RoomExecutor.get_room_by_id(booking.room_id)
        room_name = room.room_name if room else None

        booking_info = {
            "booking_id": booking.booking_id,
            "title": booking.title,
            "time_start": booking.time_start.strftime('%Y-%m-%d %H:%M:%S'),
            "time_end": booking.time_end.strftime('%Y-%m-%d %H:%M:%S'),
            "room_id": booking.room_id,
            "room_name": room_name,
            "user_ids": user_ids,
            "user_names": user_names,
            "creator_id": booking.creator_id,
            "creator_name": creator_name,
            "is_accepted": booking.is_accepted,
            "is_deleted": booking.is_deleted
        }
        return  booking_info
      
    @staticmethod
    def accept_booking(booking_id: int):
        booking = BookingExecutor.get_booking(booking_id)
        try:
            booking.is_accepted = True
            booking.is_deleted = False
            booking.deleted_at = None 

            db.session.commit()

            return BaseResponse.success('Booking accepted successfully')

        except Exception as e:
            db.session.rollback()
            raise InternalServerError(e)
    
    @staticmethod
    def reject_booking(booking_id: int):
        booking = BookingExecutor.get_booking(booking_id)
        try:
            booking.is_accepted = False
            booking.is_deleted = True
            booking.deleted_at = datetime.now()

            db.session.commit()

            return BaseResponse.success('Booking rejected successfully')

        except Exception as e:
            db.session.rollback()
            raise InternalServerError(e)
    
    @staticmethod
    def view_list_invite(page: int, per_page: int) -> list[Booking]:
        user_id=get_jwt_identity()
        bookings=BookingExecutor.view_list_invite(page,per_page,user_id)
        list_booking_invite=BookingService.show_list_booking(bookings)
        return list_booking_invite
        
        # return bookings
    
    @staticmethod
    def user_confirm_booking(booking_id: int):
        user_id = get_jwt_identity()
        booking_user = BookingExecutor.get_booking_user(booking_id, user_id)
        try:
            booking_user.is_attending = True

            db.session.commit()

            return BaseResponse.success('Invitation successfully confirmed')

        except Exception as e:
            db.session.rollback()
            raise InternalServerError(e)
        
    @staticmethod
    def user_decline_booking(booking_id: int):
        user_id = get_jwt_identity()
        booking_user = BookingExecutor.get_booking_user(booking_id, user_id)
        try:
            booking_user.is_attending = False

            db.session.commit()

            return BaseResponse.success('Invitation successfully declined')

        except Exception as e:
            db.session.rollback()
            raise InternalServerError(e)