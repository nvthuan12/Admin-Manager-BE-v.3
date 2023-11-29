from project.database.excute.room import RoomExecutor
from math import ceil
from project.models import Room
from werkzeug.exceptions import Conflict, BadRequest, NotFound
from typing import Optional

class RoomService:
    @staticmethod
    def get_paginated_rooms(page, per_page):
        items, total_items, total_pages = RoomExecutor.get_paginated_rooms(page, per_page)
        
        return {
            "rooms": [item.serialize() for item in items],
            "total_items": total_items,
            "current_page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    
    @staticmethod
    def get_room_detail(room_id: int) -> Optional[Room]:
        return RoomExecutor.get_room_detail(room_id)
    
    @staticmethod
    def create_room(data):
        room_name = data.get("room_name")
        is_blocked = data.get("is_blocked", False)
        description = data.get("description")

        existing_room = RoomExecutor.get_room_by_name(room_name)
        if existing_room:
            raise Conflict("Room already exists")

        new_room = Room(room_name=room_name, description=description, is_blocked=is_blocked)
        RoomExecutor.add_room(new_room)

    @staticmethod
    def update_room(room_id, data):
        room_name = data.get("room_name")

        existing_room = RoomExecutor.get_room_by_name(room_name)
        if existing_room:
            raise BadRequest("Room name already exists")

        room_to_update = Room.query.get(room_id)

        if not room_to_update:
            raise NotFound("Room not found")

        room_to_update.room_name = room_name
        RoomExecutor.commit()

    @staticmethod
    def delete_room(room_id, data):
        room_to_delete = RoomExecutor.get_room_by_id(room_id)

        if not room_to_delete:
            raise NotFound("Room not found")

        if room_to_delete.is_blocked:
            raise BadRequest("Cannot block locked rooms")

        description = data.get("description")

        bookings_to_delete = RoomExecutor.get_bookings_by_room_id(room_id)

        RoomExecutor.soft_delete_room_and_bookings(room_to_delete, bookings_to_delete, description)

        return {"message": "Room and associated bookings blocked successfully"}
    
    @staticmethod
    def open_room(room_id, data):
        room_to_open = RoomExecutor.get_room_by_id(room_id)

        if not room_to_open:
            raise NotFound("Room not found")

        if not room_to_open.is_blocked:
            raise BadRequest("Room is already open")

        description = data.get("description")

        bookings_to_open = RoomExecutor.get_bookings_by_room_id(room_id)

        RoomExecutor.open_room(room_to_open, bookings_to_open, description)

        return {"message": "Room and associated bookings opened successfully"}

    @staticmethod
    def get_status_rooms(page, per_page):
        paginated_rooms, total_items, total_pages = RoomExecutor.get_rooms_with_status(page, per_page)

        return {
            "rooms": [room.serialize() for room in paginated_rooms],
            "total_items": total_items,
            "current_page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
        

    @staticmethod
    def search_rooms(page, per_page, search_name):
        paginated_rooms, total_items, total_pages = RoomExecutor.search_rooms_in_db(page, per_page, search_name)

        return {
            "rooms": [room.serialize() for room in paginated_rooms],
            "total_items": total_items,
            "current_page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    
    