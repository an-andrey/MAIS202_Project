import eventlet
eventlet.monkey_patch()

# Only import after monkey patch
from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True, port=3000)