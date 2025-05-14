from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import joblib
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Load AI model safely
try:
    model = joblib.load('model.pkl') if os.path.exists('model.pkl') else None
    if model:
        print("Model loaded successfully")
    else:
        print("Model failed to load")
except Exception as e:
    print(f"⚠️ Error loading model: {str(e)}")
    model = None

# ----------------------- Models -----------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='core')  # Core user role by default

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    activity = db.Column(db.String(100), nullable=False)
    activity_type = db.Column(db.String(50))
    float_days = db.Column(db.Integer)
    primary_resource = db.Column(db.String(50))
    delay_probability = db.Column(db.Float)
    planned_duration = db.Column(db.Integer, nullable=False)
    actual_duration = db.Column(db.Integer, nullable=False)
    predicted_duration = db.Column(db.Integer)
    predicted_start = db.Column(db.Date)
    predicted_finish = db.Column(db.Date)
    planned_expense = db.Column(db.Float)
    labor_units = db.Column(db.Integer)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))

# ----------------------- Authentication -----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin_user():
    with app.app_context():
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(
                name='Admin',
                email='admin@example.com',
                password=generate_password_hash('admin123', method='pbkdf2:sha256'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created")

# ----------------------- Routes -----------------------

# Home Route - redirects to login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login_register.html', mode='login')

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'warning')
            return redirect(url_for('register'))

        # Role is set to 'core' by default for new users
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            role='core'  # Automatically assign 'core' role
        )

        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))

    return render_template('login_register.html', mode='register')

# Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'core':
        projects = Project.query.all()
        return render_template('core_dashboard.html', projects=projects)  # Core users see the dashboard
    else:
        projects = Project.query.all()
        return render_template('admin_dashboard.html', projects=projects)  # Admin sees full dashboard

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# ----------------------- Project Management -----------------------

# Admin can add projects
@app.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    if current_user.role != 'admin':
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        return render_template('add_project.html')

    try:
        # Capture form data
        new_project = Project(
            activity=request.form.get('activity'),
            activity_type=request.form.get('activity_type'),
            float_days=int(request.form.get('float_days', 0)),
            primary_resource=request.form.get('primary_resource'),
            planned_duration=int(request.form.get('planned_duration')),
            actual_duration=int(request.form.get('actual_duration')),
            predicted_duration=int(request.form.get('predicted_duration', 0)),
            predicted_start=datetime.strptime(request.form.get('predicted_start'), '%Y-%m-%d'),
            predicted_finish=datetime.strptime(request.form.get('predicted_finish'), '%Y-%m-%d'),
            planned_expense=float(request.form.get('planned_expense', 0)),
            labor_units=int(request.form.get('labor_units', 0)),
            admin_id=current_user.id
        )

        # Predict Delay Probability using the model
        if model:
            input_data = pd.DataFrame([[new_project.planned_duration, new_project.actual_duration]],
                                      columns=['planned_duration', 'actual_duration'])
            new_project.delay_probability = model.predict(input_data)[0]

            # Use the model to predict the duration based on delay probability
            delay_factor = (new_project.delay_probability / 100) + 1
            new_project.predicted_duration = round(new_project.planned_duration * delay_factor)

        # Commit the new project to the database
        db.session.add(new_project)
        db.session.commit()
        flash('Project added successfully', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Invalid input format: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding project: {str(e)}', 'danger')

    return redirect(url_for('dashboard'))

# ----------------------- Initialization -----------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()  # Create the admin user on startup
    app.run(host='0.0.0.0', port=5000, debug=True)





