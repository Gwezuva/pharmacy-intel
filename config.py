import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///pharmacy.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    