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
from datetime import datetime
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
def update_booking_endpoint(booking_id):
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
def delete_booking(booking_id):
    try:
        booking = Booking.query.get(booking_id)

        if not booking:
            raise NotFound('Booking not found')

        room_status = Room.query.filter_by(
            room_id=booking.room_id).value(Room.status)

        if room_status:
            raise BadRequest(
                'Cannot delete the booking, the room is currently in use')

        BookingUser.query.filter_by(booking_id=booking.booking_id).delete()
        db.session.delete(booking)
        db.session.commit()
        return jsonify({'message': 'Booking deleted successfully'})
    except IntegrityError:
        db.session.rollback()
        raise InternalServerError()
