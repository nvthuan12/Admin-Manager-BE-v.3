from flask import Blueprint, request, jsonify
from project import db
from project.models.booking import Booking
from project.models.room import Room
from project.models.booking_user import BookingUser
from flask_jwt_extended import JWTManager, jwt_required
from project.api.v1.has_permission import has_permission
from datetime import datetime
from werkzeug.exceptions import BadRequest, NotFound, Conflict, InternalServerError
from itertools import islice
from math import ceil

room_blueprint = Blueprint('room_controller', __name__)

@room_blueprint.route("/rooms", methods=["GET"])
@jwt_required()
@has_permission("view")
def get_rooms():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        all_rooms = Room.query.all()

        start = (page - 1) * per_page
        end = start + per_page
        paginated_rooms = list(islice(all_rooms, start, end))

        current_time = datetime.now()

        for room in paginated_rooms:
            current_bookings = Booking.query.filter(
                Booking.room_id == room.room_id,
                Booking.time_start <= current_time,
                Booking.time_end >= current_time
            ).all()

            room.status = bool(current_bookings)
            db.session.commit()
        
        total_items = len(all_rooms)
        total_pages = ceil(total_items / per_page)

        return jsonify({
            "rooms": [room.serialize() for room in paginated_rooms],
            "total_items": total_items,
            "current_page": page,
            "per_page": per_page,
            "total_pages": total_pages
        })

    except Exception as e:
        raise InternalServerError('Internal Server Error') from e

@room_blueprint.route("/rooms", methods=["POST"])
@jwt_required()
@has_permission("create")
def create_room():
    data = request.get_json()
    room_name = data.get("room_name")
    status = data.get("status", 0)

    if not room_name or room_name.isspace():
        raise BadRequest("Room name cannot be empty")

    existing_room = Room.query.filter_by(room_name=room_name).first()
    if existing_room:
        raise Conflict("Room already exists")

    new_room = Room(room_name=room_name, status=status)
    db.session.add(new_room)
    db.session.commit()

    return jsonify({"message": "Room created successfully"})


@room_blueprint.route("/rooms/<int:room_id>", methods=["PUT"])
@jwt_required()
@has_permission("update")
def update_room(room_id):
    data = request.get_json()
    room_name = data.get("room_name")

    if not room_name or room_name.isspace():
        raise BadRequest("Room name cannot be empty")

    existing_room = Room.query.filter(
        Room.room_id != room_id, Room.room_name == room_name).first()
    if existing_room:
        raise BadRequest("Room name already exists")

    room_to_update = Room.query.get(room_id)

    if not room_to_update:
        raise NotFound("Room not found")

    room_to_update.room_name = room_name
    db.session.commit()
    return jsonify({"message": "Room updated successfully"})


@room_blueprint.route("/rooms/<int:room_id>", methods=["DELETE"])
@jwt_required()
@has_permission("delete")
def delete_room(room_id):
    room_to_delete = Room.query.get(room_id)

    if not room_to_delete:
        raise NotFound("Room not found")

    if room_to_delete.status == 1:
        raise BadRequest("Cannot delete a busy room")

    bookings_to_delete = Booking.query.filter_by(room_id=room_id).all()
    booking_ids = [booking.booking_id for booking in bookings_to_delete]

    BookingUser.query.filter(BookingUser.booking_id.in_(
        booking_ids)).delete(synchronize_session=False)

    for booking in bookings_to_delete:
        db.session.delete(booking)

    db.session.delete(room_to_delete)
    db.session.commit()

    return jsonify({"message": "Room and associated bookings deleted successfully"})
