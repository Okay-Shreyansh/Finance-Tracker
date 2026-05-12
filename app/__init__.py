from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    # Import and register blueprints
    from app.auth import auth_bp
    from app.main import main_bp
    from app.transactions import transactions_bp
    from app.budget import budget_bp
    from app.analytics import analytics_bp
    from app.categories import categories_bp
    from app.insights import insights_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    app.register_blueprint(budget_bp, url_prefix='/budget')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(categories_bp, url_prefix='/categories')
    app.register_blueprint(insights_bp, url_prefix='/insights')

    return app