import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "FLASK_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_URL")
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            'ssl': {
                'ca': 'ca.pem'
            }
        }
    }