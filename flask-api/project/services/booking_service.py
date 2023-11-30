from project.database.excute.booking import BookingExecutor
from project.models import Room, Booking
from project.api.common.base_response import BaseResponse
from werkzeug.exceptions import BadRequest, InternalServerError
from flask import request
from datetime import datetime, timedelta
from typing import List

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
            room = Room.query.filter_by(room_id=booking.room_id).first()
            room_name = room.room_name if room else None
            booking_info = {
                "booking_id": booking.booking_id,
                "title": booking.title,
                "time_start": booking.time_start.strftime('%Y-%m-%d %H:%M:%S'),
                "time_end": booking.time_end.strftime('%Y-%m-%d %H:%M:%S'),
                "room_name": room_name,
                "user_name": user_names
            }
            list_bookings.append(booking_info)

        return list_bookings