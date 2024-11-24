import eventlet
eventlet.monkey_patch()

from flask import Flask
from app.config import Config
from app.extensions import init_extensions

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    with app.app_context():
        # Initialize extensions
        init_extensions(app)

        # Register blueprints
        from app.routes.auth import auth
        from app.routes.main import main
        from app.routes.movie import movie
        
        app.register_blueprint(auth)
        app.register_blueprint(main)
        app.register_blueprint(movie)

    return app