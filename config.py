import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # base configuration
    SECRET_KEY = os.getenv("SECRET_APP_KEY")
    SHARED_SECRET = os.getenv("SHARED_SECRET")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE")  # set the database URI
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")  # set the upload folder
    SAML_SP = os.getenv("SAML_SP")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    COOKIE_ISSUING_FILE = os.getenv("COOKIE_ISSUING_FILE")
    INSTITUTION_CODE = os.getenv("INSTITUTION_CODE")
    SITE_URL = os.getenv("SITE_URL")
    LOG_DIR = os.getenv("LOG_DIR")
    ALMA_SERVER = os.getenv("ALMA_SERVER")
    SMTP_ADDRESS = os.getenv("SMTP_ADDRESS")

    CELERY = {
        'broker_url': 'redis://127.0.0.1:6379',
        'result_backend': 'db+' + os.getenv("DATABASE"),
    }
