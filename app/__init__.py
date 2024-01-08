from flask import Flask
from app.extensions import db
from config import Config
from celery import Celery, Task


# Create the Flask app
def create_app(config_class=Config):
    app = Flask(__name__)  # Create the Flask app
    app.config.from_object(config_class)  # Load the configuration file

    # Initialize Flask extensions here
    celery_init_app(app)  # Initialize Celery
    db.init_app(app)  # Initialize the database

    # Register blueprints here
    with app.app_context():
        from app.upload import bp as upload_bp  # Import the upload blueprint
        app.register_blueprint(upload_bp)  # Register the upload blueprint

    # shell context for flask cli
    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": db}

    return app


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
