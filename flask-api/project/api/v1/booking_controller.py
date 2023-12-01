from flask import Blueprint, request, jsonify
from project import db
from project.models.user import User
from project.models.booking import Booking
from project.models.room import Room
from project.models.booking_user import BookingUser
from flask_jwt_extended import JWTManager, jwt_required
from project.api.v1.has_permission import has_permission
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, NotFound, Conflict, InternalServerError
from project.api.common.base_response import BaseResponse
from project.services.booking_service import BookingService
from datetime import datetime, timedelta
from typing import Dict



booking_blueprint = Blueprint('booking_controller', __name__)


@booking_blueprint.route("/bookings", methods=["GET"])
@jwt_required()
@has_permission("view")
def get_bookings() -> dict:
    try:
        response_data: dict = BookingService.get_bookings_in_date_range()
        return BaseResponse.success(response_data)

    except BadRequest as e:
        return BaseResponse.error(e)
    except InternalServerError as e:
        return BaseResponse.error(e)


@booking_blueprint.route("/bookings", methods=["POST"])
@jwt_required()
@has_permission("create")
def book_room_endpoint() -> dict:
    try:
        data = request.get_json()
        response_data: dict = BookingService.book_room(data)

        return response_data

    except BadRequest as e:
        return BaseResponse.error(e)

    except Conflict as e:
        return BaseResponse.error(e)

    except InternalServerError as e:
        return BaseResponse.error(e)

@booking_blueprint.route("/bookings/<int:booking_id>", methods=["PUT"])
@jwt_required()
@has_permission("update")
def update_booking_endpoint(booking_id: int):
    try:
        data = request.get_json()
        response_data = BookingService.update_booking(booking_id, data)
        return response_data

    except BadRequest as e:
        return BaseResponse.error(e)

    except Conflict as e:
        return BaseResponse.error(e)

    except NotFound as e:
        return BaseResponse.error(e)

    except InternalServerError as e:
        return BaseResponse.error(e)

@booking_blueprint.route("/bookings/<int:booking_id>", methods=["DELETE"])
@jwt_required()
@has_permission("delete")
def delete_booking(booking_id: int) -> Dict:
    try:
        response_data = BookingService.delete_booking_service(booking_id)
        return response_data
    except NotFound as e:
        return BaseResponse.error(e)
    
    except BadRequest as e:
        return BaseResponse.error(e)
    
    except IntegrityError:
        db.session.rollback()
        return BaseResponse.error(e)
    
@booking_blueprint.route("/bookings/search_users", methods=["GET"])
@jwt_required()
@has_permission("search")
def Search_booking_users():
    start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date')
    user_ids =request.args.getlist('user_ids')

    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else start_date + timedelta(days=6)
    print("user_id:",user_ids)
    bookings = Booking.query.join(BookingUser).filter(
        Booking.is_deleted == False,
        Booking.time_start >= start_date,
        Booking.time_start < end_date,
        BookingUser.user_id.in_(user_ids)
    ).all()
    
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

@booking_blueprint.route("/bookings/search_room/<int:room_id>", methods=["GET"])
@jwt_required()
@has_permission("search")
def Search_booking_room(room_id: int):
    start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date')
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else start_date + timedelta(days=6)
    print("room_id:",room_id)
    bookings = Booking.query.filter(
        Booking.is_deleted == False,
        Booking.time_start >= start_date,
        Booking.time_start < end_date,
        Booking.room_id== room_id
    ).all()
    
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