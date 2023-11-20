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

booking_blueprint = Blueprint('booking_controller', __name__)

@booking_blueprint.route("/bookings", methods=["GET"])
@jwt_required()
def get_bookings():
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        bookings = Booking.query.join(Room).join(BookingUser).join(User).with_entities(
            Booking.booking_id,
            Booking.room_id,
            Booking.time_start,
            Booking.time_end,
            Room.room_name,
            BookingUser.user_id,
            User.user_name
            
        ).all()

        paginated_bookings = bookings.paginate(page=page, per_page=per_page, error_out=False)


        grouped_bookings = {}

        for booking in paginated_bookings.items:
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

        result = {
            "bookings": list(grouped_bookings.values()),
            "total_pages": paginated_bookings.pages,
            "current_page": paginated_bookings.page
        }
        return jsonify(result)
    except Exception as e:
        raise InternalServerError(description='Internal Server Error') from e


@booking_blueprint.route("/bookings", methods=["POST"])
@jwt_required()
@has_permission("admin")
def book_room():
    data = request.get_json()
    room_id = data.get('room_id')
    time_start = data.get('time_start')
    time_end = data.get('time_end')
    user_ids = data.get('user_id')

    if not user_ids:
        raise BadRequest(description='No staff members have been added to the meeting yet')

    if time_start == time_end:
        raise BadRequest(description='Invalid time input')

    if time_start is not None and time_end is not None and time_start < time_end:
        existing_booking = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.time_end >= time_start,
            Booking.time_start <= time_end
        ).first()

        if existing_booking:
            raise Conflict(description='Room is already booked for this time')

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
            raise InternalServerError(description='Internal Server Error') from e
    else:
        raise BadRequest(description='Invalid time input')


@booking_blueprint.route("/bookings/<int:booking_id>", methods=["PUT"])
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
            raise BadRequest(description='Invalid time input')

        existing_booking = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.time_end >= time_start,
            Booking.time_start <= time_end
        ).first()

        if existing_booking and existing_booking.booking_id != booking_id:
            raise Conflict(description='Room is already booked for this time')

        try:
            booking = Booking.query.get(booking_id)

            if booking is None:
                raise NotFound(description='Booking not found')

            booking.room_id = room_id
            booking.time_start = time_start
            booking.time_end = time_end

            if not user_ids:
                raise BadRequest(description='At least one employee must be selected')

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
            raise InternalServerError(description='Internal Server Error') from e
    else:
        raise BadRequest(description='Invalid time input or missing user_id')



@booking_blueprint.route("/bookings/<int:booking_id>", methods=["DELETE"])
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
            raise NotFound(description='Booking not found')
    except IntegrityError as e:
        db.session.rollback()
        raise InternalServerError(description='IntegrityError: Cannot delete the booking, it might be in use') from e