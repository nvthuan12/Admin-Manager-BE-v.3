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

booking_blueprint = Blueprint('booking_controller', __name__)

@booking_blueprint.route("/bookings", methods=["GET"])
@jwt_required()
def get_bookings():
    try:
        bookings = Booking.query.join(Room).join(BookingUser).join(User).with_entities(
            Booking.booking_id,
            Booking.room_id,
            Booking.title,
            Booking.time_start,
            Booking.time_end,
            Room.room_name,
            BookingUser.user_id,
            User.user_name
        ).all()

        grouped_bookings = defaultdict(lambda: {
            "booking_id": None,
            "user_name": [],
            "room_id": None,
            "room_name": None,
            "title": None,
            "time_end": None,
            "time_start": None,
            "user_id": []
        })

        for booking in bookings:
            booking_id = booking.booking_id
            grouped_bookings[booking_id]["booking_id"] = booking_id
            grouped_bookings[booking_id]["user_id"].append(booking.user_id)
            grouped_bookings[booking_id]["user_name"].append(booking.user_name)
            grouped_bookings[booking_id]["room_id"] = booking.room_id
            grouped_bookings[booking_id]["room_name"] = booking.room_name
            grouped_bookings[booking_id]["title"] = booking.title 
            grouped_bookings[booking_id]["time_end"] = booking.time_end.strftime('%Y-%m-%d %H:%M:%S')
            grouped_bookings[booking_id]["time_start"] = booking.time_start.strftime('%Y-%m-%d %H:%M:%S')

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        start = (page - 1) * per_page
        end = start + per_page

        paginated_grouped_bookings = list(islice(grouped_bookings.values(), start, end))

        total_items = len(grouped_bookings)
        total_pages = ceil(total_items / per_page)

        result = {
            "bookings": paginated_grouped_bookings,
            "total_items": total_items,
            "current_page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
        return jsonify(result)
    except Exception as e:
        raise InternalServerError()

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
        raise BadRequest('Invalid time input. End time must be greater than start time.')

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

    if time_start is not None and time_end is not None and user_ids is not None:

        if time_end <= time_start:
            raise BadRequest('Invalid time input')

        existing_booking = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.time_end >= time_start,
            Booking.time_start <= time_end
        ).first()

        if existing_booking and existing_booking.booking_id != booking_id:
            raise Conflict('Room is already booked for this time')

        try:
            booking = Booking.query.get(booking_id)

            if booking is None:
                raise NotFound('Booking not found')

            booking.room_id = room_id
            booking.title = title
            booking.time_start = time_start
            booking.time_end = time_end

            if not user_ids:
                raise BadRequest('At least one user must be selected')

            for user_booking in booking.booking_user:
                db.session.delete(user_booking)

            for user_id in user_ids:
                user_booking = BookingUser(
                    user_id=user_id, booking_id=booking.booking_id)
                db.session.add(user_booking)

            db.session.commit()
            return jsonify({'message': 'Booking updated successfully'})
        except Exception as e:
            print(e)
            db.session.rollback()
            raise InternalServerError('Internal Server Error') from e
    else:
        raise BadRequest('Invalid time input or missing user_id')

@booking_blueprint.route("/bookings/<int:booking_id>", methods=["DELETE"])
@jwt_required()
@has_permission("delete")
def delete_booking(booking_id):
    try:
        booking = Booking.query.get(booking_id)

        if booking:
            room_status = Room.query.get(booking.room_id).status

            if room_status:
                raise BadRequest('Cannot delete the booking, the room is currently in use')

            BookingUser.query.filter_by(
                booking_id=booking.booking_id).delete()
            db.session.delete(booking)
            db.session.commit()
            return jsonify({'message': 'Booking deleted successfully'})
        else:
            raise NotFound('Booking not found')
    except IntegrityError as e:
        db.session.rollback()
        raise InternalServerError('Internal Server Error') from e