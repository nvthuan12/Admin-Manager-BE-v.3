import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    TOKEN_EXPIRATION_DAYS = os.environ.get('TOKEN_EXPIRATION_DAYS')

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    TOKEN_EXPIRATION_DAYS = os.environ.get('TOKEN_EXPIRATION_DAYS')

class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
