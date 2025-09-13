import os

class Config:
    # MySQL Database Configuration
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'jie201225'
    DB_NAME = os.environ.get('DB_NAME') or 'user'

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOW_STOCK_THRESHOLD = 10  # Example threshold for low-stock alerts
    SCHEDULER_API_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecret'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
