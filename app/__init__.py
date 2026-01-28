# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
import os

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.secret_key = 'clave_super_secreta_indescifrable'

    # Configuración de Base de Datos (SQLite)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mFUyG9cgq2Pzz2@localhost/pathfinder_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Configuración de Login
    login_manager.login_view = 'views.login'
    login_manager.init_app(app)

    # Importar Modelos (Para que se creen las tablas)
    from app.models import User, Route

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Importar Blueprints
    from app.api.routes import api_bp
    from app.views.frontend import views_bp

    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(views_bp, url_prefix='/')

    # Crear Tablas y Usuario Admin por defecto
    with app.app_context():
        db.create_all()
        create_admin_user()

    return app


def create_admin_user():
    from app.models import User
    # Verificar si existe el admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
        new_admin = User(username='admin', password=hashed_pw, role='admin')
        db.session.add(new_admin)
        db.session.commit()
        print(">>> Usuario 'admin' creado con contraseña 'admin123'")