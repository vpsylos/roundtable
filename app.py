from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
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
    computers = db.relationship('Computer', backref='assigned_user', lazy=True)
    tickets = db.relationship('Ticket', backref='ticket_user', lazy=True)

class Computer(db.Model):
    __tablename__ = 'computer'
    
    id = db.Column(db.Integer, primary_key=True)  # Primary key
    computer_id = db.Column(db.String(50), unique=True, nullable=False)  # Unique identifier (serial number)
    model = db.Column(db.String(100))  # Model of the computer
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key for user assignment
    location = db.Column(db.String(50))  # Location (office, home, HCS, Recycling Center)
    room = db.Column(db.String(50))  # Room number or identifier
    company = db.Column(db.String(100))  # Company of the computer
    cpu = db.Column(db.String(100))  # CPU specifications
    ram = db.Column(db.Integer)  # RAM in GB
    storage = db.Column(db.Integer)  # Storage in GB
    os = db.Column(db.String(100))  # Operating system
    date_inventoried = db.Column(db.DateTime)  # Date when the computer was inventoried
    price = db.Column(db.Float)  # Price of the computer
    
    user = db.relationship('User', backref='assigned_computers', lazy=True)  # Renamed backref to avoid conflict

class Ticket(db.Model):
    __tablename__ = 'ticket'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for computer association
    computer_id = db.Column(db.Integer, db.ForeignKey('computer.id'), nullable=True)  # Nullable for user association
    issue_summary = db.Column(db.String(200), nullable=False)  # Summary of the issue reported in the ticket
    status = db.Column(db.String(20), default='Open')  # Status of the ticket (e.g., Open, Closed)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp when the ticket was created
    appointment_time = db.Column(db.DateTime)  # Scheduled appointment time for addressing the issue

    # Relationships for ticket associations
    computer = db.relationship('Computer', backref='computers_tickets', lazy=True)
    user = db.relationship('User', backref='users_tickets', lazy=True)


# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    open_tickets = Ticket.query.filter(Ticket.status != 'Closed').order_by(Ticket.appointment_time).all()
    return render_template('home.html', tickets=open_tickets)

@app.route('/add_user', methods=['GET', 'POST'])
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
def add_computer():
    if request.method == 'POST':
        computer_id = request.form['computer_id']
        model = request.form['model']
        user_id = request.form['user_id']
        
        location = request.form['location']
        room = request.form.get('room')
        company = request.form.get('company')
        cpu = request.form.get('cpu')
        ram = int(request.form.get('ram')) if request.form.get('ram') else None
        storage = int(request.form.get('storage')) if request.form.get('storage') else None
        os = request.form.get('os')
        
        date_inventoried = request.form.get('date_inventoried')
        
        price = float(request.form.get('price')) if request.form.get('price') else None
        
        user = User.query.get(user_id)
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('add_computer'))
        
        new_computer = Computer(
            computer_id=computer_id,
            model=model,
            assigned_user_id=user_id,
            location=location,
            room=room,
            company=company,
            cpu=cpu,
            ram=ram,
            storage=storage,
            os=os,
            date_inventoried=datetime.strptime(date_inventoried, '%Y-%m-%d') if date_inventoried else None,
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
    
    users = User.query.all()
    return render_template('add_computer.html', users=users)


@app.route('/add_ticket', methods=['GET', 'POST'])
def add_ticket():
    if request.method == 'POST':
        issue_summary = request.form['issue_summary']
        user_id = request.form['user_id']
        computer_id = request.form.get('computer_id')  # Optional
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        status = request.form['status']
        
        # Combine date and time
        appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        
        new_ticket = Ticket(
            issue_summary=issue_summary,
            user_id=user_id,
            computer_id=computer_id,
            appointment_time=appointment_datetime,
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
    return render_template('add_ticket.html', users=users, computers=computers)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
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


@app.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if request.method == 'POST':
        ticket.issue_summary = request.form['issue_summary']
        ticket.user_id = request.form['user_id']
        ticket.computer_id = request.form.get('computer_id')
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        ticket.appointment_time = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        ticket.status = request.form['status']
        
        try:
            db.session.commit()
            flash('Ticket updated successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating ticket: {str(e)}', 'error')
    
    users = User.query.all()
    computers = Computer.query.all()
    return render_template('edit_ticket.html', ticket=ticket, users=users, computers=computers)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=user)

@app.route('/computer/<int:computer_id>')
def computer_profile(computer_id):
    computer = Computer.query.get_or_404(computer_id)
    return render_template('computer_profile.html', computer=computer)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    users = User.query.filter(User.full_name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%')).all()
    computers = Computer.query.filter(Computer.computer_id.ilike(f'%{query}%')).all()
    return render_template('search_results.html', query=query, users=users, computers=computers)

if __name__ == '__main__':
    app.run(debug=True)
