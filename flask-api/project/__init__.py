import os
from flask import Flask, request
from project.config import BaseConfig
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from celery import Celery, shared_task
from pyfcm import FCMNotification
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from flask_apscheduler import APScheduler

app=Flask(__name__)

CORS(app, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = BaseConfig.SQLALCHEMY_DATABASE_URI
app.config['JWT_SECRET_KEY'] = BaseConfig.JWT_SECRET_KEY
app.config['MAIL_SERVER'] = BaseConfig.MAIL_SERVER
app.config['MAIL_PORT'] = BaseConfig.MAIL_PORT
app.config['MAIL_USERNAME'] = BaseConfig.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = BaseConfig.MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = BaseConfig.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = BaseConfig.MAIL_USE_SSL
app.config['MAIL_DEFAULT_SENDER'] = BaseConfig.MAIL_DEFAULT_SENDER
app.config['SCHEDULER_API_ENABLED'] = BaseConfig.SCHEDULER_API_ENABLED
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

mail = Mail(app)

cred = credentials.Certificate('./rikkei-intern-web-2023-firebase-adminsdk-anzt6-68e93153ae.json')
firebase_admin.initialize_app(cred)
push_service = FCMNotification(api_key=BaseConfig.FCM_SERVER_KEY)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

scheduler =  APScheduler()
scheduler.init_app(app)
scheduler.start()


app.config['CELERY_BROKER_URL'] =  BaseConfig.CELERY_BROKER_URL
app.config['CELERY_RESULT_BACKEND'] = BaseConfig.CELERY_RESULT_BACKEND
app.config['MAIL_SERVER'] = BaseConfig.MAIL_SERVER
app.config['MAIL_PORT'] = BaseConfig.MAIL_PORT
app.config['MAIL_USERNAME'] = BaseConfig.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = BaseConfig.MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = BaseConfig.MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = BaseConfig.MAIL_USE_SSL
app.config['MAIL_DEFAULT_SENDER'] = BaseConfig.MAIL_DEFAULT_SENDER

mail = Mail(app)

# push_service = FCMNotification(api_key=BaseConfig.FCM_SERVER_KEY)
# cred = credentials.Certificate('./fir-d8b4e-firebase-adminsdk-a7lj0-a377d2856c.json')
# firebase_admin.initialize_app(cred)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

scheduler =  APScheduler()
scheduler.init_app(app)
scheduler.start()

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
with app.app_context():
    from project import models
    db.create_all()

from celery import shared_task

@shared_task(ignore_result=False)
def add_together(a: int, b: int) -> int:
    return a + b

@app.post("/add")
def start_add() -> dict[str, object]:
    a = request.form.get("a", type=int)
    b = request.form.get("b", type=int)
    result = add_together.delay(a, b)
    return {"result_id": result.id}
    
from project.api.v1.login_controller import login_blueprint
from project.api.v1.user_controller import user_blueprint
from project.api.v1.room_controller import room_blueprint
from project.api.v1.booking_controller import booking_blueprint

app.register_blueprint(login_blueprint, url_prefix='/v1')
app.register_blueprint(user_blueprint, url_prefix='/v1')
app.register_blueprint(room_blueprint, url_prefix='/v1')
app.register_blueprint(booking_blueprint, url_prefix='/v1')

from project.api.common.base_response import BaseResponse
from werkzeug.exceptions import HTTPException 
app.register_error_handler(HTTPException, BaseResponse.error)