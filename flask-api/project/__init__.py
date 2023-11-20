import os
from flask import Flask
from flask import Config
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

app=Flask(__name__)
CORS(app, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']

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
app.register_blueprint(login_blueprint, url_prefix='/v1')
app.register_blueprint(user_blueprint, url_prefix='/v1')
app.register_blueprint(room_blueprint, url_prefix='/v1')
app.register_blueprint(booking_blueprint, url_prefix='/v1')
from project.api.common.error_handle import handle_werkzeug_exception
from werkzeug.exceptions import HTTPException 
app.register_error_handler(HTTPException, handle_werkzeug_exception)