import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://localhost:5000')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    DATABASE_PATH = BASE_DIR / os.getenv('DATABASE_PATH', 'database/shop.db')
    EXCEL_PATH = BASE_DIR / os.getenv('EXCEL_PATH', 'exports/orders.xlsx')
    PHOTOS_PATH = BASE_DIR / 'web/static/assets/photos'
    
    SSL_CERT_PATH = BASE_DIR / os.getenv('SSL_CERT_PATH', 'certs/cert.pem')
    SSL_KEY_PATH = BASE_DIR / os.getenv('SSL_KEY_PATH', 'certs/key.pem')

    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500
    MAX_PRICE = 1000000
    MIN_PRICE = 0.01
    
    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set")
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.SSL_CERT_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.PHOTOS_PATH.mkdir(parents=True, exist_ok=True)
        return True

config = Config()
