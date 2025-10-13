from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Date

db = SQLAlchemy()

class Member(db.Model):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    dob = Column(String)
    designation = Column(String)
    office_tel = Column(String)
    mobile = Column(String)
    bank_account = Column(String)
    aadhaar = Column(String)
    pan = Column(String)
    nominee_name = Column(String)
    nominee_age = Column(String)
    relationship = Column(String)
    other_society = Column(String)
    fee_receipt = Column(String)
    other_details = Column(String)
    application_date = Column(String)

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