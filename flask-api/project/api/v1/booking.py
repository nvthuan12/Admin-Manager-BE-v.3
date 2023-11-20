from flask import Blueprint, request, jsonify
import project.api.common.utils.exceptions as exceptions
from project import app,db
from project.models.user import User
from project.models.role import Role
from project.models.booking import Booking
from project.models.room import Room
from project.models.booking_user import BookingUser
from project.models.role_has_permission import RoleHasPermission
from project.models.permission import Permission
from project.models.user_has_role import UserHasRole
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, set_access_cookies, unset_jwt_cookies,get_jwt_identity,get_jwt
from project.api.v1.has_permission import has_permission, get_role_names
from sqlalchemy.exc import IntegrityError
from collections import defaultdict


@app.route("/bookings", methods=["GET"])
@jwt_required()
def get_bookings():
    try:
        bookings = Booking.query.join(Room).join(BookingUser).join(User).with_entities(
            Booking.booking_id,
            Booking.room_id,
            Booking.time_start,
            Booking.time_end,
            Room.room_name,
            BookingUser.user_id,
            User.user_name
            
        ).all()

        grouped_bookings = {}

        for booking in bookings:
            booking_dict = booking._asdict()
            booking_id = booking_dict["booking_id"]

            if booking_id not in grouped_bookings:
                grouped_bookings[booking_id] = {
                    "booking_id": booking_id,
                    "user_name": [],
                    "room_id": None,
                    "room_name": None,
                    "time_end": None,
                    "time_start": None,
                    "user_id": []
                }
            grouped_bookings[booking_id]["user_id"].append(
                booking_dict["user_id"])
            grouped_bookings[booking_id]["user_name"].append(
                booking_dict["user_name"])
            grouped_bookings[booking_id]["room_id"] = booking_dict["room_id"]
            grouped_bookings[booking_id]["room_name"] = booking_dict["room_name"]
            grouped_bookings[booking_id]["time_end"] = booking_dict["time_end"].strftime(
                '%Y-%m-%d %H:%M:%S')
            grouped_bookings[booking_id]["time_start"] = booking_dict["time_start"].strftime(
                '%Y-%m-%d %H:%M:%S')

        result = {"bookings": list(grouped_bookings.values())}
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route("/bookings", methods=["POST"])
@jwt_required()
@has_permission("admin")
def book_room():
    data = request.get_json()
    room_id = data.get('room_id')
    time_start = data.get('time_start')
    time_end = data.get('time_end')
    user_ids = data.get('user_id')

    if not user_ids:
        return jsonify({'error': 'No staff members have been added to the meeting yet'}), 400

    if time_start == time_end:
        return jsonify({'error': 'Invalid time input'}), 400

    if time_start is not None and time_end is not None and time_start < time_end:
        existing_booking = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.time_end >= time_start,
            Booking.time_start <= time_end
        ).first()

        if existing_booking:
            return jsonify({'error': 'Room is already booked for this time'}), 400

        try:
            new_booking = Booking(
                room_id=room_id, time_start=time_start, time_end=time_end)
            db.session.add(new_booking)
            db.session.commit()

            for user_id in user_ids:
                employee_booking = BookingUser(
                    user_id=user_id, booking_id=new_booking.booking_id)
                db.session.add(employee_booking)

            db.session.commit()
            return jsonify({'message': 'Booking created successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Internal Server Error'}), 500
    else:
        return jsonify({'error': 'Invalid time input'}), 400


@app.route("/bookings/<int:booking_id>", methods=["PUT"])
@jwt_required()
@has_permission("admin")
def update_booking(booking_id):
    data = request.get_json()
    room_id = data.get('room_id')
    time_start = data.get('time_start')
    time_end = data.get('time_end')
    user_ids = data.get('user_id')

    if time_start is not None and time_end is not None and user_ids is not None:
        if time_end <= time_start:
            return jsonify({'error': 'Invalid time input'}), 400
        existing_booking = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.time_end >= time_start,
            Booking.time_start <= time_end
        ).first()

        if existing_booking and existing_booking.booking_id != booking_id:
            return jsonify({'error': 'Room is already booked for this time'}), 400

        try:
            booking = Booking.query.get(booking_id)

            if booking is None:
                return jsonify({'error': 'Booking not found'}), 404

            booking.room_id = room_id
            booking.time_start = time_start
            booking.time_end = time_end

            if not user_ids:
                return jsonify({'error': 'At least one employee must be selected'}), 400

            for employee_booking in booking.booking_employees:
                db.session.delete(employee_booking)

            for user_id in user_ids:
                employee_booking = BookingUser(
                    user_id=user_id, booking_id=booking.booking_id)
                db.session.add(employee_booking)

            db.session.commit()
            return jsonify({'message': 'Booking updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Internal Server Error'}), 500
    else:
        return jsonify({'error': 'Invalid time input or missing user_id'}), 400



@app.route("/bookings/<int:booking_id>", methods=["DELETE"])
@jwt_required()
@has_permission("admin")
def delete_booking(booking_id):
    try:
        booking = Booking.query.get(booking_id)
        if booking:
            BookingUser.query.filter_by(
                booking_id=booking.booking_id).delete()
            db.session.delete(booking)
            db.session.commit()
            return jsonify({'message': 'Booking deleted successfully'})
        else:
            return jsonify({'error': 'Booking not found'}), 404
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': 'IntegrityError: Cannot delete the booking, it might be in use'}), 500