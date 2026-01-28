# app/views/frontend.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from app.services.data_service import DataService

views_bp = Blueprint('views', __name__)
data_service = DataService()


# --- RUTAS PÚBLICAS ---
@views_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return render_template('home.html')


@views_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('views.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('login.html')


@views_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Verificar si existe
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'warning')
        else:
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_pw, role='user')
            db.session.add(new_user)
            db.session.commit()
            flash('Cuenta creada. Por favor inicia sesión.', 'success')
            return redirect(url_for('views.login'))

    return render_template('register.html')


@views_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))


# --- RUTAS PROTEGIDAS (DASHBOARD) ---
@views_bp.route('/dashboard')
@login_required
def dashboard():
    stats = data_service.get_user_stats(current_user.id)
    return render_template('dashboard.html', user=current_user.username, stats=stats, role=current_user.role)


@views_bp.route('/calculator')
@login_required
def calculator():
    return render_template('index.html', user=current_user.username)


@views_bp.route('/history')
@login_required
def history():
    history_data = data_service.get_user_history(current_user.id)
    return render_template('history.html', user=current_user.username, history=history_data)


@views_bp.route('/docs')
def docs():
    return render_template('docs.html', user=current_user.username if current_user.is_authenticated else None)


# --- RUTAS DE ADMIN ---
@views_bp.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        return redirect(url_for('views.dashboard'))

    users = data_service.get_all_users()
    return render_template('admin.html', users=users, user=current_user.username)


@views_bp.route('/admin/delete/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('views.dashboard'))

    if user_id == current_user.id:
        flash("No puedes borrarte a ti mismo", "error")
    else:
        data_service.delete_user(user_id)
        flash("Usuario eliminado", "success")

    return redirect(url_for('views.admin_panel'))