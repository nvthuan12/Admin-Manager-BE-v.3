import os
from flask import Flask
from flask import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from project.extensions import db, migrate, bcrypt
from dotenv import load_dotenv


load_dotenv()

app=Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SQLALCHEMY_DATABASE_URI']
app.config['JWT_SECRET_KEY'] = os.environ['JWT_SECRET_KEY']

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
with app.app_context():
    from project import models
    db.create_all()
from project.api.v1.login import login_blueprint
app.register_blueprint(login_blueprint, url_prefix='/v1')