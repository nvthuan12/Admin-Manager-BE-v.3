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
from itertools import islice
from math import ceil
from collections import defaultdict
from sqlalchemy import extract
from datetime import datetime, timedelta
from project.api.common.base_response import BaseResponse
from dateutil.relativedelta import relativedelta


booking_blueprint = Blueprint('booking_controller', __name__)


@booking_blueprint.route("/bookings", methods=["GET"])
@jwt_required()
@has_permission("view")
def get_bookings():
    try:
        start_date_str = request.args.get('start_date', None)
        end_date_str = request.args.get('end_date', None)

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
        else:
            return BadRequest("Both start_date and end_date are required for date range query.")

        bookings = Booking.query.filter(
            Booking.is_deleted == False,
            Booking.time_end.between(start_date, end_date)
        ).all()

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

        return BaseResponse.success(list_bookings)
    except BadRequest as bad_request:
        raise bad_request
    except Exception as e:
        raise InternalServerError("Internal Server Error")




@booking_blueprint.route("/bookings", methods=["POST"])
@jwt_required()
@has_permission("create")
def book_room():
    data = request.get_json()
    room_id = data.get('room_id')
    title = data.get('title')
    time_start = data.get('time_start')
    time_end = data.get('time_end')
    user_ids = data.get('user_id')

    if not user_ids:
        raise BadRequest('No staff members have been added to the meeting yet')

    if time_start >= time_end:
        raise BadRequest(
            'Invalid time input. End time must be greater than start time.')

    if not (room_id and time_start and time_end and title and title.strip()):
        raise BadRequest('Invalid or empty values')
    
    # if datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S') < datetime.now():
    #     raise BadRequest('Cannot book a room for the past')

    existing_booking = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.time_end >= time_start,
        Booking.time_start <= time_end
    ).first()

    if existing_booking:
        raise Conflict('Room is already booked for this time')

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
        return jsonify({'message': 'Booking created successfully'})
    except Exception as e:
        print(e)
        db.session.rollback()
        raise InternalServerError()


@booking_blueprint.route("/bookings/<int:booking_id>", methods=["PUT"])
@jwt_required()
@has_permission("update")
def update_booking(booking_id):
    data = request.get_json()
    room_id = data.get('room_id')
    title = data.get('title')
    time_start = data.get('time_start')
    time_end = data.get('time_end')
    user_ids = data.get('user_id')

    if not user_ids:
        raise BadRequest("At least one user must be selected")

    if not (room_id and time_start and time_end and title and title.strip()):
        raise BadRequest('Invalid or empty values')

    if time_start is not None and time_end is not None and user_ids is not None:
        if time_end <= time_start:
            raise BadRequest('Invalid time input')

        existing_booking = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.time_end >= time_start,
            Booking.time_start <= time_end,
            Booking.booking_id != booking_id
        ).first()

        if existing_booking:
            raise Conflict('Room is already booked for this time')

        try:
            booking = Booking.query.get(booking_id)

            if booking is None:
                raise NotFound('Booking not found')

            booking.room_id = room_id
            booking.title = title
            booking.time_start = time_start
            booking.time_end = time_end

            BookingUser.query.filter_by(booking_id=booking_id).delete()

            for user_id in user_ids:
                user_booking = BookingUser(
                    user_id=user_id, booking_id=booking.booking_id)
                db.session.add(user_booking)

            db.session.commit()
            return jsonify({'message': 'Booking updated successfully'})
        except Exception as e:
            db.session.rollback()
            raise InternalServerError() from e
    else:
        raise BadRequest('Invalid time input or missing user_id')


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
