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

booking_blueprint = Blueprint('booking_controller', __name__)


@booking_blueprint.route("/bookings", methods=["GET"])
@jwt_required()
@has_permission("view")
def get_bookings():
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)

        week_in_month = request.args.get('week_in_month', type=int)

        if month is None or year is None:
            raise BadRequest("Month and year are required parameters.")

        bookings = Booking.query.filter(
            extract('month', Booking.time_start) == month,
            extract('year', Booking.time_start) == year
        ).join(Room).join(BookingUser).join(User).with_entities(
            Booking.booking_id,
            Booking.room_id,
            Booking.title,
            Booking.time_start,
            Booking.time_end,
            Booking.is_accepted,
            Room.room_name,
            Room.is_blocked,
            BookingUser.user_id,
            BookingUser.is_attending,
            User.user_name
        ).all()

        grouped_bookings = defaultdict(lambda: {
            "booking_id": None,
            "room_id": None,
            "title": None,
            "time_start": None,
            "time_end": None,
            "is_accepted": None,
            "room_name": None,
            "is_blocked": None,
            "user_id": [],
            "is_attending": None,
            "user_name": [] 
        })

        for booking in bookings:
            if week_in_month is not None:
                if extract('week', booking.time_start) == week_in_month:
                    process_booking(booking, grouped_bookings)
            else:
                process_booking(booking, grouped_bookings)

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        start = (page - 1) * per_page
        end = start + per_page

        paginated_grouped_bookings = list(
            islice(grouped_bookings.values(), start, end))

        total_items = len(grouped_bookings)
        total_pages = ceil(total_items / per_page)

        result = {
            "bookings": paginated_grouped_bookings,
            "total_items": total_items,
            "current_page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    except BadRequest as bad_request:
        raise bad_request
    except Exception as e:
        raise InternalServerError("Internal Server Error")

def process_booking(booking, grouped_bookings):
    booking_id = booking.booking_id
    grouped_bookings[booking_id]["booking_id"] = booking_id
    grouped_bookings[booking_id]["user_id"].append(booking.user_id)
    grouped_bookings[booking_id]["user_name"].append(booking.user_name)
    grouped_bookings[booking_id]["room_id"] = booking.room_id
    grouped_bookings[booking_id]["room_name"] = booking.room_name
    grouped_bookings[booking_id]["title"] = booking.title
    grouped_bookings[booking_id]["time_end"] = booking.time_end.strftime('%Y-%m-%d %H:%M:%S')
    grouped_bookings[booking_id]["time_start"] = booking.time_start.strftime('%Y-%m-%d %H:%M:%S')
    grouped_bookings[booking_id]["is_accepted"] = booking.is_accepted
    grouped_bookings[booking_id]["is_blocked"] = booking.is_blocked
    grouped_bookings[booking_id]["is_attending"] = booking.is_attending
    print("Attributes for booking object:", dir(booking))


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

    existing_booking = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.time_end >= time_start,
        Booking.time_start <= time_end
    ).first()

    if existing_booking:
        raise Conflict('Room is already booked for this time')

    try:
        new_booking = Booking(
            room_id=room_id, title=title, time_start=time_start, time_end=time_end)
        db.session.add(new_booking)
        db.session.commit()

        for user_id in user_ids:
            user_booking = BookingUser(
                user_id=user_id, booking_id=new_booking.booking_id)
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
