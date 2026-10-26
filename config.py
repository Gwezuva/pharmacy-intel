import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
    
    # Get the database URL
    uri = os.environ.get("DATABASE_URL", "sqlite:///pharmacy.db")
    
    # Fix for Render: SQLAlchemy requires 'postgresql://', not 'postgres://'
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False