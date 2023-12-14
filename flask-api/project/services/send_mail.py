from project import app, mail, scheduler, push_service, celery
from flask_mail import Message
from datetime import datetime, timedelta
from project.services.booking_service import BookingService
from project.models import Booking
import os


class Schedule_mail:

    @staticmethod
    def send_meeting_reminder(participants):
        # Gửi email thông báo cho từng người tham gia
        with app.app_context():
            for participant in participants:
                message = 'Booked success'
                subject = "hello...."
                msg = Message(sender=os.getenv('MAIL_DEFAULT_SENDER'),
                              recipients=[participant],
                              body=message,
                              subject=subject)
                print(f"Subject: {msg.subject}")
                print(f"Body: {msg.body}")
                mail.send(msg)
    
    @staticmethod
    def send_notification_to_users(user):
        message_title = "Meeting Reminder"
        message_body = "You have a meeting coming up soon!"
        print("đã vào",)
        push_service.notify_single_device(
            registration_id=user.fcm_token, 
            message_title=message_title, 
            message_body=message_body)

    @staticmethod
    def get_meetings_starting_soon(start_time, minutes):
        with app.app_context():
            bookings = Booking.query.filter(
                Booking.is_deleted == False,
                Booking.deleted_at == None,
                Booking.time_start == (start_time + timedelta(minutes=minutes))
            ).all()

            users = []
            for booking in bookings:
                users.extend([booking_user.user for booking_user in booking.booking_user])
            print("users", users)
            print("start_time2", start_time + timedelta(minutes=minutes))
            
            return users

    @staticmethod
    def scheduled_send():
        now = datetime.now()
        users = Schedule_mail.get_meetings_starting_soon(now, 10)
        if users:
            participants = [user.email for user in users]
            Schedule_mail.send_meeting_reminder(participants)
            for user in users:
                Schedule_mail.send_notification_to_users(user)
        pass
