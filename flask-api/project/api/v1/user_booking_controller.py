from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from project.api.v1.has_permission import has_permission
from werkzeug.exceptions import BadRequest, NotFound, Conflict, InternalServerError
from project.api.common.base_response import BaseResponse
from project.services.user_booking_service import UserBookingService
from typing import Dict

user_booking_blueprint = Blueprint('user_booking_controller', __name__)

@user_booking_blueprint.route("/user/bookings", methods=["GET"])
@jwt_required()
@has_permission("view")
def get_user_bookings() -> dict:
    try:
        response_data: dict = UserBookingService.get_bookings_in_date_range_user()
        return BaseResponse.success(response_data)

    except BadRequest as e:
        return BaseResponse.error(e)
    except InternalServerError as e:
        return BaseResponse.error(e)
    
@user_booking_blueprint.route("/user/bookings", methods=["POST"])
@jwt_required()
@has_permission("create")
def book_room_endpoint_user() -> dict:
    try:
        data = request.get_json()
        response_data: dict = UserBookingService.book_room_belong_to_user(data)

        return response_data

    except BadRequest as e:
        return BaseResponse.error(e)

    except Conflict as e:
        return BaseResponse.error(e)

    except InternalServerError as e:
        return BaseResponse.error(e)