import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # base configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE")
    SECRET_KEY = os.getenv("SECRET_APP_KEY")
    SHARED_SECRET = os.getenv("SHARED_SECRET")
    LOG_DIR = os.getenv("LOG_DIR")
    LOG_LEVEL = os.getenv("LOG_LEVEL")
    ALMA_SERVER = os.getenv("ALMA_SERVER")
    SMTP_ADDRESS = os.getenv("SMTP_ADDRESS")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SITE_URL = os.getenv("SITE_URL")
    SAML_SP = os.getenv("SAML_SP")
    COOKIE_ISSUING_FILE = os.getenv("COOKIE_ISSUING_FILE")
    COOKIE_PREFIX = os.getenv("COOKIE_PREFIX")
    SERVICE_SLUG = os.getenv("SERVICE_SLUG")
    MEMCACHED_SERVER = os.getenv("MEMCACHED_SERVER")
    INSTITUTION_CODE = os.getenv("INSTITUTION_CODE")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")

    CELERY = {
        'broker_url': 'redis://127.0.0.1:6379',
        'result_backend': 'db+' + os.getenv("DATABASE"),
    }
