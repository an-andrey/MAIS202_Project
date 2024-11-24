# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def init_extensions(app):
    db.init_app(app)
    
    # Configure login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Import here to avoid circular imports
    from app.models.user import Users
    
    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))
    
    # Configure socketio
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        ping_timeout=300,
        ping_interval=60,
        logger=True,
        engineio_logger=True
    )