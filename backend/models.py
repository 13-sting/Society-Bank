from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_no = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    balance = db.Column(db.Float, default=0.0)
    is_approved = db.Column(db.Boolean, default=False)
    address = db.Column(db.String(255))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f'<Member {self.name}>'

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., Savings, Current
    balance = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    tenure_months = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., Fixed, Recurring
    maturity_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # Credit/Debit
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))