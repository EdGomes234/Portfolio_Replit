import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///portfolio.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    
    # Proxy fix for deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Add custom filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks"""
        if text is None:
            return ''
        return text.replace('\n', '<br>\n')
    
    # Add template context processors
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # Create upload directory
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    return app

app = create_app()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Create tables and initialize data
with app.app_context():
    import models  # noqa: F401
    db.create_all()
    logging.info("Database tables created")
    
    # Create admin user if no users exist
    from models import User, Category
    if User.query.count() == 0:
        admin_user = User(
            username='edgar',
            email='edgar@portfolio.com',
            first_name='Edgar',
            last_name='Gomes',
            is_admin=True,
            bio='Desenvolvedor Full Stack apaixonado por tecnologia e inovação',
            linkedin_url='https://www.linkedin.com/in/edgar-gomes234',
            github_url='https://github.com/EdGomes234'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # Create default categories
        default_categories = [
            {'name': 'Desenvolvimento Web', 'color': '#FF6B35'},
            {'name': 'Mobile', 'color': '#28A745'},
            {'name': 'Desktop', 'color': '#007BFF'},
            {'name': 'Machine Learning', 'color': '#6F42C1'},
            {'name': 'DevOps', 'color': '#DC3545'}
        ]
        
        for cat_data in default_categories:
            category = Category(name=cat_data['name'], color=cat_data['color'])
            db.session.add(category)
        
        db.session.commit()
        logging.info("Admin user and default categories created")
