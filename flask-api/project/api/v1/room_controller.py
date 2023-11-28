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
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

room_blueprint = Blueprint('room_controller', __name__)

@room_blueprint.route("/rooms", methods=["GET"])
@jwt_required()
@has_permission("view")
def get_rooms():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        query = Room.query.paginate(page=page, per_page=per_page, error_out=False)
        paginated_rooms = query.items

        return jsonify({
            "rooms": [room.serialize() for room in paginated_rooms],
            "total_items": query.total,
            "current_page": page,
            "per_page": per_page,
            "total_pages": ceil(query.total / per_page)
        })

    except Exception as e:
        print(e)
        raise InternalServerError('Internal Server Error') from e
    
@room_blueprint.route("/rooms/<int:room_id>", methods=["GET"])
@jwt_required()
@has_permission("view")
def get_room_detail(room_id):
    try:
        room = Room.query.get_or_404(room_id)
        return jsonify(room.serialize())

    except Exception as e:
        raise InternalServerError('Internal Server Error') from e

@room_blueprint.route("/rooms", methods=["POST"])
@jwt_required()
@has_permission("create")
def create_room():
    data = request.get_json()
    room_name = data.get("room_name")
    is_blocked = data.get("is_blocked", False)
    description = data.get("description")

    if not room_name or room_name.isspace():
        raise BadRequest("Room name cannot be empty")

    existing_room = Room.query.filter_by(room_name=room_name).first()
    if existing_room:
        raise Conflict("Room already exists")

    new_room = Room(room_name=room_name, description=description, is_blocked=is_blocked)
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

@room_blueprint.route("/rooms/<int:room_id>/blocked", methods=["PUT"])
@jwt_required()
@has_permission("update")
def delete_room(room_id):
    try:
        data = request.get_json()
        description = data.get("description")

        room_to_delete = Room.query.get(room_id)

        if not room_to_delete:
            raise NotFound("Room not found")

        if room_to_delete.is_blocked:
            raise BadRequest("Cannot block locked rooms")

        bookings_to_delete = Booking.query.filter_by(room_id=room_id).all()
        for booking in bookings_to_delete:
            booking.deleted_at = datetime.utcnow()

        BookingUser.query.filter(BookingUser.booking_id.in_(
            [booking.booking_id for booking in bookings_to_delete])).delete(synchronize_session=False)

        room_to_delete.deleted_at = datetime.utcnow()
        room_to_delete.is_blocked = True
        room_to_delete.description = description

        db.session.commit()

        return jsonify({"message": "Room and associated bookings deleted (soft delete) successfully"})

    except NotFound as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@room_blueprint.route("/rooms/<int:room_id>/opened", methods=["PUT"])
@jwt_required()
@has_permission("update")
def open_room(room_id):
    try:
        data = request.get_json()
        description = data.get("description")
        is_blocked = data.get("is_blocked", 0)

        room_to_open = Room.query.get(room_id)

        if not room_to_open:
            raise NotFound("Room not found")

        if not room_to_open.is_blocked:
            raise BadRequest("Room is already open")

        room_to_open.is_blocked = is_blocked
        room_to_open.description = description
        room_to_open.deleted_at = None

        db.session.commit()

        return jsonify({"message": "Room opened successfully"})

    except NotFound as e:
        return jsonify({"error": str(e)}), 404

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@room_blueprint.route("/status_rooms", methods=["GET"])
@jwt_required()
@has_permission("view")
def get_status_rooms():
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

            room.is_blocked = bool(current_bookings)

            if room.is_blocked:
                room.description = "BUSY"
            else:
                room.description = "FREE"

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
    
@room_blueprint.route("/rooms/search", methods=["GET"])
@jwt_required()
@has_permission("view")
def search_rooms():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_name = request.args.get('name', '')

        query = Room.query.filter(or_(Room.room_name.ilike(f"%{search_name}%")) if search_name else True)
        paginated_rooms = query.paginate(page=page, per_page=per_page, error_out=False).items
        
        total_items = len(query.all())
        total_pages = ceil(len(query.all()) / per_page)
        
        return jsonify({
            "rooms": [room.serialize() for room in paginated_rooms],
            "total_items": total_items,
            "current_page": page,   
            "per_page": per_page,
            "total_pages": total_pages
        })

    except Exception as e:
        raise InternalServerError('Internal Server Error') from e
