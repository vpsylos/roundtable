from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///techsupport.db'
db = SQLAlchemy(app)
app.logger.setLevel(logging.DEBUG)
migrate = Migrate(app, db)

# Database Models
class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)  # Full name of the user
    pronouns = db.Column(db.String(20))  # User's pronouns
    role = db.Column(db.Enum('Faculty', 'Staff', 'Other'), nullable=False)  # Role of the user
    department = db.Column(db.String(100))  # Department
    office_number = db.Column(db.String(20))  # Office number
    cellphone_number = db.Column(db.String(20))  # Cellphone number
    uniID = db.Column(db.String(20), unique=True, nullable=False)  # University ID
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email address
    office_location = db.Column(db.String(100))  # Office location
    last_replaced_date = db.Column(db.DateTime)  # Last date a computer was replaced
    replacement_cycle_years = db.Column(db.Integer)  # How often a computer is to be replaced in years
    
    # Relationships to computers and tickets
    computers = db.relationship('Computer', backref='users_computers', lazy=True)
    tickets = db.relationship('Ticket', backref='users_tickets', lazy=True)

class Technician(db.Model):
    __tablename__ = 'technician'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)  # Full name of the technician
    pronouns = db.Column(db.String(20))  # Technician's pronouns
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email address
    role = db.Column(db.Enum('Technician', 'Admin'), nullable=False)  # Role of the technician

class TechnicianLogIn(UserMixin, db.Model):
    __tablename__ = 'technician_login'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.Enum('Technician', 'Admin'), nullable=False)

    def is_admin(self):
        return self.role == 'Admin'

# Define the Company model
class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# Define the Model model
class Model(db.Model):
    __tablename__ = 'model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# Define the CPU model
class CPU(db.Model):
    __tablename__ = 'cpu'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# Define the OS model
class OS(db.Model):
    __tablename__ = 'os'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Computer(db.Model):
    __tablename__ = 'computer'
    
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref='computers_companies')  # Company of the computer
    computer_id = db.Column(db.String(50), unique=True, nullable=False)  # Unique identifier (serial number)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    model = db.relationship('Model', backref='computers_models')  # Model of the computer
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key for user assignment
    assigned_user = db.relationship('User', backref='assigned_computers', lazy=True)
    location = db.Column(db.String(50))  # Location (office, home, HCS, Recycling Center)
    room = db.Column(db.String(50))  # Room number or identifier
    cpu_id = db.Column(db.Integer, db.ForeignKey('cpu.id'), nullable=False)
    cpu = db.relationship('CPU', backref='computers_cpus')  # CPU specifications
    ram = db.Column(db.Integer)  # RAM in GB
    storage = db.Column(db.Integer)  # Storage in GB
    os_id = db.Column(db.Integer, db.ForeignKey('os.id'), nullable=False)
    os = db.relationship('OS', backref='computers_oss')  # Operating system
    date_inventoried = db.Column(db.DateTime)  # Date when the computer was inventoried
    price = db.Column(db.Float)  # Price of the computer

class Ticket(db.Model):
    __tablename__ = 'ticket'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for computer association
    user = db.relationship('User', backref='tickets_users', lazy=True)
    computer_id = db.Column(db.Integer, db.ForeignKey('computer.id'), nullable=True)  # Nullable for user association
    computer = db.relationship('Computer', backref='tickets_computers', lazy=True)
    issue_summary = db.Column(db.String(200), nullable=False)  # Summary of the issue reported in the ticket
    status = db.Column(db.String(20), default='Open')  # Status of the ticket (e.g., Open, Closed)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp when the ticket was created
    appointment_time = db.Column(db.DateTime)  # Scheduled appointment time for addressing the issue
    appointment_length = db.Column(db.Integer, nullable=False)  # in minutes
    assigned_person_id = db.Column(db.Integer, db.ForeignKey('technician.id'))
    assigned_person = db.relationship('Technician', backref='tickets_technicians', lazy=True)
    location = db.Column(db.String(100), nullable=False)  # 'In House', 'At Office', or 'Remote'

# Create the database tables
with app.app_context():
    db.create_all()

# Handle logging in
login_manager = LoginManager(app)

@login_manager.user_loader
def load_technician(technician_id):
    return TechnicianLogIn.query.get(technician_id)

@app.route('/login', methods=['GET', 'POST'])
def technician_login():
    if not TechnicianLogIn.query.first():
        return redirect(url_for('create_first_admin'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        technician = TechnicianLogIn.query.filter_by(username=username).first()
        if technician and check_password_hash(technician.password, password):
            login_user(technician)
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('technician_login'))

@app.route('/create_first_admin', methods=['GET', 'POST'])
def create_first_admin():
    if request.method == 'POST':
        full_name = request.form['full_name']
        pronouns = request.form['pronouns']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        new_admin_login = TechnicianLogIn(email=email, username=username, password=generate_password_hash(password), role='Admin')
        new_admin = Technician(full_name=full_name, pronouns=pronouns, email=email, role='Admin')
        db.session.add(new_admin)
        db.session.add(new_admin_login)
        db.session.commit()
        
        return redirect(url_for('technician_login'))
    return render_template('create_first_admin.html')

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        technician = Technician.query.filter_by(email=email).first()
        if technician:
            print(technician)
            role = getattr(technician, 'role')
            new_user = TechnicianLogIn(email=email, username=username, password=generate_password_hash(password), role=role)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('technician_login'))
        else:
            return redirect(url_for('create_account'))
        
    return render_template('create_account.html')

# Decorators to ensure a user is logged in, and is an admin
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('technician_login'))
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.role == 'Admin':
            return f(*args, **kwargs)
        elif current_user.is_authenticated:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
        else:
            return redirect(url_for('technician_login'))
    return decorated_function

@app.route('/')
@login_required
def home():
    open_tickets = Ticket.query.filter(Ticket.status != 'Closed').order_by(Ticket.appointment_time).all()
    return render_template('home.html', tickets=open_tickets)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        # Capture all required fields from the form
        full_name = request.form['full_name']
        pronouns = request.form.get('pronouns')  # Optional
        role = request.form['role']
        department = request.form.get('department')  # Optional
        office_number = request.form.get('office_number')  # Optional
        cellphone_number = request.form.get('cellphone_number')  # Optional
        uniID = request.form['uniID']
        email = request.form['email']
        office_location = request.form.get('office_location')  # Optional
        last_replaced_date = request.form.get('last_replaced_date')  # Optional
        replacement_cycle_years = request.form.get('replacement_cycle_years')  # Optional
        
        # Create a new User instance with the captured data
        new_user = User(
            full_name=full_name,
            pronouns=pronouns,
            role=role,
            department=department,
            office_number=office_number,
            cellphone_number=cellphone_number,
            uniID=uniID,
            email=email,
            office_location=office_location,
            last_replaced_date=datetime.strptime(last_replaced_date, '%Y-%m-%d') if last_replaced_date else None,
            replacement_cycle_years=int(replacement_cycle_years) if replacement_cycle_years else None
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding user: {str(e)}', 'error')
    
    return render_template('add_user.html')

@app.route('/add_computer', methods=['GET', 'POST'])
@login_required
def add_computer():
    if request.method == 'POST':
        computer_id = request.form['computer_id']
        model_name = request.form['model']
        user_id = request.form['user_id']
        location = request.form['location']
        room = request.form.get('room')
        company_name = request.form.get('company')
        cpu_name = request.form.get('cpu')
        ram = int(request.form.get('ram')) if request.form.get('ram') else None
        storage = int(request.form.get('storage')) if request.form.get('storage') else None
        os_name = request.form.get('os')
        date_inventoried = datetime.strptime(request.form.get('date_inventoried'), '%Y-%m-%d') if request.form.get('date_inventoried') else None
        price = float(request.form.get('price')) if request.form.get('price') else None

        # Get or create company
        company = Company.query.filter_by(name=company_name).first()
        if not company:
            company = Company(name=company_name)
            db.session.add(company)
            db.session.commit()

        # Get or create model
        model = Model.query.filter_by(name=model_name).first()
        if not model:
            model = Model(name=model_name)
            db.session.add(model)
            db.session.commit()

        # Get or create cpu
        cpu = CPU.query.filter_by(name=cpu_name).first()
        if not cpu:
            cpu = CPU(name=cpu_name)
            db.session.add(cpu)
            db.session.commit()

        # Get or create os
        os = OS.query.filter_by(name=os_name).first()
        if not os:
            os = OS(name=os_name)
            db.session.add(os)
            db.session.commit()

        # Get user
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('add_computer'))

        # Create new computer
        new_computer = Computer(
            computer_id=computer_id,
            model=model,
            assigned_user=user,
            location=location,
            room=room,
            company=company,
            cpu=cpu,
            ram=ram,
            storage=storage,
            os=os,
            date_inventoried=date_inventoried,
            price=price
        )

        try:
            db.session.add(new_computer)
            db.session.commit()
            flash('Computer added successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding computer: {str(e)}', 'error')

    return render_template('add_computer.html', companies=Company.query.all(), models=Model.query.all(), cpus=CPU.query.all(), oss=OS.query.all(), users=User.query.all())


@app.route('/add_ticket', methods=['GET', 'POST'])
@login_required
def add_ticket():
    if request.method == 'POST':
        issue_summary = request.form['issue_summary']
        user_id = request.form['user_id']
        computer_id = request.form.get('computer_id')  # Optional
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        status = request.form['status']
        appointment_length = request.form['appointment_length']  # Added this line
        assigned_person_id = request.form['assigned_person_id']  # Added this line
        location = request.form['location']  # Added this line
        
        # Combine date and time
        appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        
        new_ticket = Ticket(
            issue_summary=issue_summary,
            user_id=user_id,
            computer_id=computer_id,
            appointment_time=appointment_datetime,
            appointment_length=appointment_length,  # Added this line
            assigned_person_id=assigned_person_id,  # Added this line
            location=location,  # Added this line
            status=status
        )
        
        try:
            db.session.add(new_ticket)
            db.session.commit()
            flash('Ticket added successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding ticket: {str(e)}', 'error')
    
    users = User.query.all()
    computers = Computer.query.all()
    technicians = Technician.query.all()
    return render_template('add_ticket.html', users=users, computers=computers, technicians=technicians)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.pronouns = request.form.get('pronouns')
        user.role = request.form['role']
        user.department = request.form.get('department')
        user.office_number = request.form.get('office_number')
        user.cellphone_number = request.form.get('cellphone_number')
        user.uniID = request.form['uniID']
        user.email = request.form['email']
        user.office_location = request.form.get('office_location')
        
        last_replaced_date = request.form.get('last_replaced_date')
        if last_replaced_date:
            user.last_replaced_date = datetime.strptime(last_replaced_date, "%Y-%m-%d")
        else:
            user.last_replaced_date = None
        
        replacement_cycle_years = request.form.get('replacement_cycle_years')
        user.replacement_cycle_years = int(replacement_cycle_years) if replacement_cycle_years else None
        
        try:
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
            
    return render_template('edit_user.html', user=user)

@app.route('/edit_computer/<int:computer_id>', methods=['GET', 'POST'])
@login_required
def edit_computer(computer_id):
    computer = Computer.query.get_or_404(computer_id)

    if request.method == 'POST':
        computer.computer_id = request.form['computer_id']
        model_name = request.form['model']
        user_id = request.form['user_id']
        location = request.form['location']
        room = request.form.get('room')
        company_name = request.form.get('company')
        cpu_name = request.form.get('cpu')
        ram = int(request.form.get('ram')) if request.form.get('ram') else None
        storage = int(request.form.get('storage')) if request.form.get('storage') else None
        os_name = request.form.get('os')
        date_inventoried = datetime.strptime(request.form.get('date_inventoried'), '%Y-%m-%d') if request.form.get('date_inventoried') else None
        price = float(request.form.get('price')) if request.form.get('price') else None

        # Get or create company
        company = Company.query.filter_by(name=company_name).first()
        if not company:
            company = Company(name=company_name)
            db.session.add(company)
            db.session.commit()
        computer.company = company

        # Get or create model
        model = Model.query.filter_by(name=model_name).first()
        if not model:
            model = Model(name=model_name)
            db.session.add(model)
            db.session.commit()
        computer.model = model

        # Get or create cpu
        cpu = CPU.query.filter_by(name=cpu_name).first()
        if not cpu:
            cpu = CPU(name=cpu_name)
            db.session.add(cpu)
            db.session.commit()
        computer.cpu = cpu

        # Get or create os
        os = OS.query.filter_by(name=os_name).first()
        if not os:
            os = OS(name=os_name)
            db.session.add(os)
            db.session.commit()
        computer.os = os

        # Get user
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('edit_computer', computer_id=computer_id))
        computer.assigned_user = user

        computer.location = location
        computer.room = room
        computer.ram = ram
        computer.storage = storage
        computer.date_inventoried = date_inventoried
        computer.price = price

        try:
            db.session.commit()
            flash('Computer updated successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating computer: {str(e)}', 'error')

    users = User.query.all()
    return render_template('edit_computer.html', computer=computer, users=users)

@app.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if request.method == 'POST':
        ticket.issue_summary = request.form['issue_summary']
        ticket.user_id = request.form['user_id']
        ticket.computer_id = request.form.get('computer_id')
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        ticket.appointment_time = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        ticket.appointment_length = request.form['appointment_length']
        ticket.status = request.form['status']
        ticket.assigned_person_id = request.form['assigned_person_id']
        ticket.location = request.form['location']
        
        try:
            db.session.commit()
            flash('Ticket updated successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating ticket: {str(e)}', 'error')
    
    users = User.query.all()
    computers = Computer.query.all()
    technicians = Technician.query.all()
    return render_template('edit_ticket.html', ticket=ticket, users=users, computers=computers, technicians=technicians)

@app.route('/user/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=user)

@app.route('/computer/<int:computer_id>')
@login_required
def computer_profile(computer_id):
    computer = Computer.query.get_or_404(computer_id)
    return render_template('computer_profile.html', computer=computer)

@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('q', '')
    users = User.query.filter(User.full_name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%')).all()
    computers = Computer.query.filter(Computer.computer_id.ilike(f'%{query}%')).all()
    return render_template('search_results.html', query=query, users=users, computers=computers)

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin():
    users = User.query.all()
    computers = Computer.query.all()
    tickets = Ticket.query.all()
    
    if request.method == 'POST':
        user_email = request.form.get('user_email')
        computer_id = request.form.get('computer_id')
        ticket_id = request.form.get('ticket_id')
        
        if user_email:
            user = User.query.filter_by(email=user_email).first()
            if user:
                # Delete all computers associated with the user
                computers_to_delete = Computer.query.filter_by(assigned_user_id=user.id).all()
                for computer in computers_to_delete:
                    # Delete all tickets associated with the computer
                    tickets_to_delete = Ticket.query.filter_by(computer_id=computer.id).all()
                    for ticket in tickets_to_delete:
                        db.session.delete(ticket)
                    db.session.delete(computer)
            db.session.delete(user)
        elif computer_id:
            computer = Computer.query.get_or_404(computer_id)
            if computer:
                # Delete all tickets associated with the computer
                tickets_to_delete = Ticket.query.filter_by(computer_id=computer.id).all()
                for ticket in tickets_to_delete:
                    db.session.delete(ticket)
            db.session.delete(computer)
        
        db.session.commit()
        return redirect(url_for('admin'))
    
    return render_template('admin.html', data={'users': users, 'computers': computers, 'tickets': tickets})

@app.route('/admin/edit_dropdown_menus', methods=['GET', 'POST'])
@admin_required
def edit_dropdown_menus():
    if request.method == 'POST':
        # Get the form data
        companies = request.form.getlist('companies')
        models = request.form.getlist('models')
        cpus = request.form.getlist('cpus')
        oss = request.form.getlist('oss')

        # Add any new items
        if 'add_company' in request.form:
            new_company = request.form.get('new_company')
            if new_company:
                company = Company.query.filter_by(name=new_company).first()
                if not company:
                    company = Company(name=new_company)
                    db.session.add(company)
                    db.session.commit()

        if 'add_model' in request.form:
            new_model = request.form.get('new_model')
            if new_model:
                model = Model.query.filter_by(name=new_model).first()
                if not model:
                    model = Model(name=new_model)
                    db.session.add(model)
                    db.session.commit()

        if 'add_cpu' in request.form:
            new_cpu = request.form.get('new_cpu')
            if new_cpu:
                cpu = CPU.query.filter_by(name=new_cpu).first()
                if not cpu:
                    cpu = CPU(name=new_cpu)
                    db.session.add(cpu)
                    db.session.commit()

        if 'add_os' in request.form:
            new_os = request.form.get('new_os')
            if new_os:
                os = OS.query.filter_by(name=new_os).first()
                if not os:
                    os = OS(name=new_os)
                    db.session.add(os)
                    db.session.commit()

        if 'delete_company' in request.form:
            delete_company = request.form.get('delete_company')
            if delete_company:
                company = Company.query.filter_by(name=delete_company).first()
                if company:
                    db.session.delete(company)
                    db.session.commit()

        if 'delete_model' in request.form:
            delete_model = request.form.get('delete_model')
            if delete_model:
                model = Model.query.filter_by(name=delete_model).first()
                if model:
                    db.session.delete(model)
                    db.session.commit()

        if 'delete_cpu' in request.form:
            delete_cpu = request.form.get('delete_cpu')
            if delete_cpu:
                cpu = CPU.query.filter_by(name=delete_cpu).first()
                if cpu:
                    db.session.delete(cpu)
                    db.session.commit()

        if 'delete_os' in request.form:
            delete_os = request.form.get('delete_os')
            if delete_os:
                os = OS.query.filter_by(name=delete_os).first()
                if os:
                    db.session.delete(os)
                    db.session.commit()

    # Get the current dropdown menu items
    companies = Company.query.all()
    models = Model.query.all()
    cpus = CPU.query.all()
    oss = OS.query.all()

    return render_template('admin_edit_dropdown_menus.html', 
                           companies=companies, 
                           models=models, 
                           cpus=cpus, 
                           oss=oss)

@app.route('/admin/edit_technicians', methods=['GET', 'POST'])
@admin_required
def edit_technicians():
    if request.method == 'POST':
        if 'add_technician' in request.form:
            full_name = request.form['full_name']
            pronouns = request.form['pronouns']
            email = request.form['email']
            role = request.form['role']
            if role not in ['Admin', 'Technician']:
                flash('Please select an appropriate role for the technician.', 'error')
                return redirect(url_for('edit_technicians'))
            if full_name and email:
                technician = Technician.query.filter_by(email=email).first()
                if not technician:
                    technician = Technician(full_name=full_name, pronouns=pronouns, email=email, role=role)
                    print(technician.role)
                    db.session.add(technician)
                    db.session.commit()
        elif 'delete_technician_submit' in request.form:
            delete_technician = request.form.get('delete_technician')
            if delete_technician:
                technician = Technician.query.get(delete_technician)
                technician_login = TechnicianLogIn.query.filter_by(email=technician.email).first()
                if technician:
                    db.session.delete(technician)
                if technician_login:
                    db.session.delete(technician_login)
                    db.session.commit()

    technicians = Technician.query.all()
    return render_template('admin_edit_technicians.html', technicians=technicians, current_user=current_user)

if __name__ == '__main__':
    create_admin_user()
    app.run(debug=True)
