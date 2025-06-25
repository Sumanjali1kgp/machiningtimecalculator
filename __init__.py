from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Initialize the database
db = SQLAlchemy()

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Configure the application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-please-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///machining.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database with the app
    db.init_app(app)
    
    from .models import base_operation, turning, facing, drilling, milling

    
    # Import and register blueprints here if you have any
    # from .routes import main_bp
    # app.register_blueprint(main_bp)
    
    # Initialize database tables
    with app.app_context():
        db.create_all()
    
    return app

# Make db and create_app available when importing from the package
__all__ = ['db', 'create_app']
