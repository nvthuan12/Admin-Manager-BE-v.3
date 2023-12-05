import os
from flask import Flask
from project.config import BaseConfig
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

app=Flask(__name__)
CORS(app, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = BaseConfig.SQLALCHEMY_DATABASE_URI
app.config['JWT_SECRET_KEY'] = BaseConfig.JWT_SECRET_KEY

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
with app.app_context():
    from project import models
    db.create_all()
    
from project.api.v1.login_controller import login_blueprint
from project.api.v1.user_controller import user_blueprint
from project.api.v1.room_controller import room_blueprint
from project.api.v1.booking_controller import booking_blueprint
from project.api.v1.user_booking_controller import user_booking_blueprint

app.register_blueprint(login_blueprint, url_prefix='/v1')
app.register_blueprint(user_blueprint, url_prefix='/v1')
app.register_blueprint(room_blueprint, url_prefix='/v1')
app.register_blueprint(booking_blueprint, url_prefix='/v1')
app.register_blueprint(user_booking_blueprint, url_prefix='/v1')

from project.api.common.base_response import BaseResponse
from werkzeug.exceptions import HTTPException 
app.register_error_handler(HTTPException, BaseResponse.error)