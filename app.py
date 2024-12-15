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
    
    id = db.Column(db.Integer, primary_key=True)
    computer_id = db.Column(db.String(50), unique=True, nullable=False)  # Unique identifier for the computer
    model = db.Column(db.String(100))  # Model of the computer
    
    # Foreign key to associate with a user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

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
    computer = db.relationship('Computer', backref='tickets', lazy=True)

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
        name = request.form['name']
        department = request.form['department']
        email = request.form['email']
        phone = request.form['phone']
        
        new_user = User(name=name, department=department, email=email, phone=phone)
        
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
        
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('add_computer'))
        
        new_computer = Computer(computer_id=computer_id, model=model, user_id=user_id)
        
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
    users = User.query.filter(User.name.ilike(f'%{query}%') | User.email.ilike(f'%{query}%')).all()
    computers = Computer.query.filter(Computer.computer_id.ilike(f'%{query}%')).all()
    return render_template('search_results.html', query=query, users=users, computers=computers)

if __name__ == '__main__':
    app.run(debug=True)
