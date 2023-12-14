from flask_mail import Message
import os
from project import mail, app, celery
from project.api.common.base_response import BaseResponse
import smtplib
from project.database.excute.room import RoomExecutor
from project.models import User, Booking


class EmailSender:
    @celery.task
    async def send_email_inviting_join_the_meeting(user_email, title, time_start, time_end, room_name, attendees):
        try:
                msg = Message(f'[LỜI MỜI THAM GIA]: {title}', sender=os.getenv('MAIL_USERNAME'), recipients=[user_email])
                msg.body = f'Thông báo cuộc họp\n\n' \
                           f'Phòng họp: {room_name}\n' \
                           f'Thời gian: {time_start} - {time_end}\n' \
                           f'Người tham gia:\n{",\n".join(attendees)}\n\n' \
                           f'Bạn được thêm vào tham gia cuộc họp. Vào trang lời mời tham gia cuộc họp của mình để xác nhận tham gia.'
                await mail.send.apply_async(args=[msg])
                
        except smtplib.SMTPException as e:
            return await BaseResponse.error(e)
        
    @celery.task
    async def send_email_accepting_the_scheduled(user_email, title, time_start, time_end, room_name, attendees):
        try:
                msg = Message(f'[XÁC NHẬN]: {title}', sender=os.getenv('MAIL_USERNAME'), recipients=[user_email])
                msg.body = f'Có một cuộc họp đã được chấp nhận!\n\n' \
                           f'Phòng họp: {room_name}\n' \
                           f'Thời gian: {time_start} - {time_end}\n' \
                           f'Người tham gia:\n{",\n".join(attendees)}' 
                await mail.send.apply_async(args=[msg])

        except smtplib.SMTPException as e:
            return await BaseResponse.error(e)
    
    @staticmethod
    def send_mail_reminder(booking: Booking, user: User):
        try:
            with app.app_context():
                print("đã vào mail",)
                attendees=[booking_user.user.user_name for booking_user in booking.booking_user]
                room= RoomExecutor.get_room_by_id(booking.room_id)
                msg = Message(f'[THÔNG BÁO]: {booking.title}', sender=os.getenv('MAIL_USERNAME'), recipients=[user.email])
                msg.body = f'Thông báo cuộc họp\n\n' \
                           f'Cuộc họp còn 10 phút nữa sẽ bắt đầu!\n\n' \
                           f'Phòng họp: {room.room_name}\n' \
                           f'Thời gian: {booking.time_start} - {booking.time_end}\n' \
                           f'Người tham gia:\n{",\n".join(attendees)}' 
                mail.send(msg)
                
        except InternalServerError as e:
            return BaseResponse.error(e)