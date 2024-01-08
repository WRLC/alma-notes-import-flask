import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # base configuration
    SECRET_KEY = os.getenv("SECRET_APP_KEY")
    SHARED_SECRET = os.getenv("SHARED_SECRET")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE")  # set the database URI
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")  # set the upload folder
    saml_sp = os.getenv("SAML_SP")
    cookie_issuing_file = os.getenv("COOKIE_ISSUING_FILE")
    institution_code = os.getenv("INSTITUTION_CODE")
    site_url = os.getenv("SITE_URL")
    log_dir = os.getenv("LOG_DIR")
    ALMA_SERVER = os.getenv("ALMA_SERVER")

    CELERY = {
        'broker_url': 'redis://127.0.0.1:6379',
        'result_backend': 'db+' + os.getenv("DATABASE"),
    }
