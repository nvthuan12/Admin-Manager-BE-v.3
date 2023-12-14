from flask_mail import Message
import requests
from project import mail, app, celery, push_service, scheduler
from werkzeug.exceptions import InternalServerError
from project.api.common.base_response import BaseResponse
from project.database.excute.room import RoomExecutor
from project.database.excute.booking import BookingExecutor
from datetime import datetime, timedelta
from project.services.email_service import EmailSender


class PushNotification:

    @staticmethod
    def send_notification_reminder(fcm_token: str, message_title: str, message_body: str ):
        print("đã vào đây,",message_title)
        push_service.notify_single_device(
            registration_id=fcm_token, 
            message_title=message_title, 
            message_body=message_body)
        
    @staticmethod
    @scheduler.task( trigger="cron", id="interval_1",minute="*")
    def scheduled_send():
        with app.app_context():
            curent_time = datetime.now().replace(second=0, microsecond=0)
            time_cooming= curent_time+ timedelta(minutes=10)
            print("time:",time_cooming)
            bookings=BookingExecutor.get_list_meeting_cooming(time_cooming)
            if bookings:
                users = []
                for booking in bookings:
                    users.extend([booking_user.user for booking_user in booking.booking_user])  
                    for user in users:
                        if user.fcm_token:
                            PushNotification.send_notification_reminder(
                                fcm_token=user.fcm_token,
                                message_title=booking.title,
                                message_body="The meeting will take place in 10 minutes ")
                        EmailSender.send_mail_reminder(booking, user) 