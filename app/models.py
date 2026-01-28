# app/models.py
from app import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' o 'user'

    # Relación: Un usuario tiene muchas rutas
    routes = db.relationship('Route', backref='owner', lazy=True, cascade="all, delete-orphan")


class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_node = db.Column(db.String(100), nullable=False)
    end_node = db.Column(db.String(100), nullable=False)
    distance = db.Column(db.Float, nullable=False)
    path_json = db.Column(db.Text, nullable=False)  # Guardamos el array como texto JSON
    weather_summary = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.now)

    # Llave foránea para saber de quién es la ruta
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)