from project.database.excute.room import RoomExecutor
from math import ceil
from project import db
from project.models import Room, Booking
from werkzeug.exceptions import Conflict, BadRequest, NotFound, InternalServerError
from typing import Optional, Dict, List
from project.api.common.base_response import BaseResponse

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
    def create_room(data: Dict) -> Dict:
        room_name: str = data.get("room_name")
        is_blocked: Optional[bool] = data.get("is_blocked", False)
        description: Optional[str] = data.get("description")

        new_room = Room(room_name=room_name, description=description, is_blocked=is_blocked)

        validate_errors = new_room.validate_all_fields()
        if validate_errors:
           return BaseResponse.error_validate(validate_errors)

        existing_room: Optional[Room] = RoomExecutor.get_room_by_name(room_name)
        if existing_room:
            raise Conflict("Room already exists")

        
        RoomExecutor.add_room(new_room)

        return BaseResponse.success(message = "Room created successfully")

    @staticmethod
    def update_room(room_id: int, data: Dict) -> None:
        room_name = data.get("room_name")

        room_to_update = Room.query.get(room_id)

        if not room_to_update:
            raise NotFound("Room not found")
        
        validate_room_name=Room.validate_room_name(room_name)
        if validate_room_name:
            return BaseResponse.error_validate(validate_room_name)
        
        existing_room = RoomExecutor.get_room_by_name(room_name)
        if existing_room:
            raise BadRequest("Room name already exists")

        room_to_update.room_name = room_name
        db.commit()
        return BaseResponse.success(message="update room successfully!")
        

    @staticmethod
    def delete_room(room_id: int, data: Optional[Dict]) -> Dict:
        try:
            room_to_delete: Room = RoomExecutor.get_room_by_id(room_id)
            description = data.get("description")

            validate_description=Room.validate_description(description)
            if validate_description:
                return BaseResponse.error_validate(validate_description)

            if not room_to_delete:
                raise NotFound("Room not found")

            if room_to_delete.is_blocked:
                raise BadRequest("Cannot block locked rooms")

            description: Optional[str] = data.get("description") if data else None

            bookings_to_delete: List[Booking] = RoomExecutor.get_bookings_by_room_id(room_id)

            RoomExecutor.soft_delete_room_and_bookings(room_to_delete, bookings_to_delete, description)

            
            return BaseResponse.success(message="Room and associated bookings blocked successfully")

        except Exception as e:
            raise InternalServerError(e)
    
    @staticmethod
    def open_room(room_id: int, data: Dict) -> Dict:
        room_to_open = RoomExecutor.get_room_by_id(room_id)

        description = data.get("description")

        validate_description=Room.validate_description(description)
        if validate_description:
            return BaseResponse.error_validate(validate_description)

        if not room_to_open:
            raise NotFound("Room not found")

        if not room_to_open.is_blocked:
            raise BadRequest("Room is already open")

        description = data.get("description")

        bookings_to_open = RoomExecutor.get_bookings_by_room_id(room_id)

        RoomExecutor.open_room(room_to_open, bookings_to_open, description)

        return BaseResponse.success(message="Room and associated bookings opened successfully")

    @staticmethod
    def get_status_rooms(page: int, per_page: int):
        paginated_rooms, total_items, total_pages = RoomExecutor.get_rooms_with_status(page, per_page)

        return {
            "rooms": [room.serialize() for room in paginated_rooms],
            "total_items": total_items,
            "current_page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
        

    @staticmethod
    def search_rooms(page: int, per_page: int, search_name: Optional[str]) -> Dict[str, int]:
        paginated_rooms, total_items, total_pages = RoomExecutor.search_rooms_in_db(page, per_page, search_name)

        return {
            "rooms": [room.serialize() for room in paginated_rooms],
            "total_items": total_items,
            "current_page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
        
    