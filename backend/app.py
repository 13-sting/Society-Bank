import requests
# Fast2SMS API Key (replace with your actual API key)
FAST2SMS_API_KEY = 'YOUR_FAST2SMS_API_KEY'

def send_sms_fast2sms(phone: str, message: str) -> None:
    url = 'https://www.fast2sms.com/dev/bulkV2'
    headers = {
        'authorization': FAST2SMS_API_KEY
    }
    payload = {
        'sender_id': 'FSTSMS',
        'message': message,
        'language': 'english',
        'route': 'v3',
        'numbers': phone
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        print('SMS response:', response.json())
    except Exception as e:
        print('Error sending SMS:', e)

import random
import datetime
from functools import wraps
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_cors import CORS
from typing import List
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from models import db, Member, Account, Loan, Deposit, Transaction, Announcement

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///society_bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_email_password'

CORS(app)

def send_email(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = to_email

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(EMAIL_HOST_USER, [to_email], msg.as_string())
        server.quit()
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/')
def index():
    announcements: List[Announcement] = Announcement.query.all()
    return render_template('index.html', announcements=announcements)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        member = Member.query.filter_by(username=username, password=password).first()
        if member and member.is_approved:
            session['member_id'] = member.id
            session['name'] = member.name
            flash('Login successful!', 'success')
            return redirect(url_for('member_dashboard'))
        else:
            flash('Invalid username, password, or not approved.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

def login_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'member_id' not in session:
                flash('Please login first')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('is_admin'):
                flash('Admin access required.')
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/admin', methods=['GET', 'POST'])
@admin_required()
def admin():
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        action = request.form.get('action')
        member = Member.query.get(member_id)
        if member:
            if action == 'approve':
                member.is_approved = True
                db.session.commit()
                flash(f'Member {member.name} approved successfully.', 'success')
            elif action == 'reject':
                db.session.delete(member)
                db.session.commit()
                flash(f'Member {member.name} rejected and removed.', 'success')
        else:
            flash('Member not found.', 'error')
    unapproved_members = Member.query.filter_by(is_approved=False).all()
    return render_template('admin.html', unapproved_members=unapproved_members)

@app.route('/admin/announcements', methods=['GET', 'POST'])
@login_required()
def manage_announcements():
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            announcement = Announcement(message=message)
            db.session.add(announcement)
            db.session.commit()
            flash('Announcement added!')
        return redirect(url_for('manage_announcements'))
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('admin_announcements.html', announcements=announcements)

@app.route('/members')
@login_required()
def list_members():
    members = Member.query.all()
    member_details = []
    for member in members:
        loans = Loan.query.filter_by(member_id=member.id).all()
        # Find the member's account
        account = Account.query.filter_by(member_id=member.id).first()
        transactions = Transaction.query.filter_by(account_id=account.id).all() if account else []
        fixed_deposits = Deposit.query.filter_by(member_id=member.id).all()
        member_details.append({
            'member': member,
            'loans': loans,
            'transactions': transactions,
            'fixed_deposits': fixed_deposits
        })
    return render_template('list_members.html', member_details=member_details)

@app.route('/accounts')
@login_required()
def list_accounts():
    accounts = Account.query.all()
    return render_template('accounts.html', accounts=accounts)

@app.route('/loans')
@login_required()
def list_loans():
    loans = Loan.query.all()
    return render_template('loans.html', loans=loans)

@app.route('/deposits')
@login_required()
def list_deposits():
    deposits = Deposit.query.all()
    return render_template('deposits.html', deposits=deposits)

@app.route('/transactions')
@login_required()
def list_transactions():
     transactions = Transaction.query.all()
     return render_template('transactions.html', transactions=transactions)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            account_no = request.form.get('account_no')
            email = request.form.get('email')
            phone = request.form.get('phone')
            balance = float(request.form.get('balance', 0.0))
            new_member = Member(
                name=name,
                account_no=account_no,
                email=email,
                phone=phone,
                balance=balance
            )
            db.session.add(new_member)
            db.session.commit()
            flash('Registration successful! Please wait for approval.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'Admin@123':
            session['is_admin'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid admin credentials.', 'error')
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/admin/add-member', methods=['GET', 'POST'])
@admin_required()
def admin_add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        account_no = request.form.get('account_no')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        balance = float(request.form.get('balance', 0.0))

        # Generate username and password
        username = account_no
        password = f"Society{random.randint(1000,9999)}"

        # Check for duplicate account_no or username
        existing_member = Member.query.filter((Member.account_no == account_no) | (Member.username == username)).first()
        if existing_member:
            flash('Account number or username already exists. Please use a unique account number.', 'error')
            return redirect(url_for('admin_add_member'))

        # Save new member
        new_member = Member(
            name=name,
            account_no=account_no,
            email=email,
            phone=phone,
            balance=balance,
            is_approved=True,
            address=address,
            dob=dob,
            gender=gender,
            username=username,
            password=password
        )
        db.session.add(new_member)
        db.session.commit()
        # Send SMS with login details
        sms_message = f"Welcome to Society Bank! Your Username: {username}, Password: {password}. Please use these to log in."
        send_sms_fast2sms(phone, sms_message)
        flash('Member added successfully! Login details sent via SMS.', 'success')
        db.session.commit()
        # Send SMS with login details
        sms_message = f"Welcome to Society Bank! Your Username: {username}, Password: {password}. Please use these to log in."
        send_sms_fast2sms(phone, sms_message)
        flash('Member added successfully! Login details sent via SMS.', 'success')
        return redirect(url_for('list_members'))
    return render_template('admin_add_member.html')
    return render_template('admin_add_member.html')

@app.route('/member-dashboard')
@login_required()
def member_dashboard():
    member_id = session.get('member_id')
    member = Member.query.get(member_id)
    # Find the member's account
    account = Account.query.filter_by(member_id=member_id).first() if member else None
    transactions = Transaction.query.filter_by(account_id=account.id).all() if account else []
    loans = Loan.query.filter_by(member_id=member_id).all() if member else []
    # Dummy shares data, replace with actual model/query if available
    shares = []
    return render_template('member_dashboard.html', member=member, transactions=transactions, loans=loans, shares=shares)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)