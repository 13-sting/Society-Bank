from fastapi import FastAPI, Request, Form, Depends, status, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from db import SessionLocal, engine, Base
import models
import requests
import smtplib
from email.mime.text import MIMEText
import random
from typing import List

app = FastAPI()

# Create the database tables
Base.metadata.create_all(bind=engine)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="templates")

FAST2SMS_API_KEY = 'YOUR_FAST2SMS_API_KEY'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_email_password'

def send_sms_fast2sms(phone: str, message: str) -> None:
    url = 'https://www.fast2sms.com/dev/bulkV2'
    headers = {'authorization': FAST2SMS_API_KEY}
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

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Home page
@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    announcements = db.query(models.Announcement).all()
    return templates.TemplateResponse("index.html", {"request": request, "announcements": announcements})

# Login
@app.get("/login", response_class=HTMLResponse, name="login")
def login_form(request: Request):
    # Pass an empty error or info if needed
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    member = db.query(models.Member).filter_by(username=username, password=password).first()
    if not member or not member.is_approved:
        # Show error message on login page
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials or not approved."})
    response = RedirectResponse(url="/member-dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="member_id", value=str(member.id))
    response.set_cookie(key="name", value=member.name)
    return response

# Logout
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("member_id")
    response.delete_cookie("name")
    return response

# Admin login
@app.get("/admin-login", response_class=HTMLResponse, name="admin_login")
def admin_login_form(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})

@app.post("/admin-login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == 'admin' and password == 'Admin@123':
        response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="is_admin", value="true")
        return response
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid admin credentials."})

# Admin dashboard
@app.get("/admin", response_class=HTMLResponse, name="admin")
def admin_dashboard(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    unapproved_members = db.query(models.Member).filter_by(is_approved=False).all()
    return templates.TemplateResponse("admin.html", {"request": request, "unapproved_members": unapproved_members})

@app.post("/admin")
def admin_action(request: Request, member_id: int = Form(...), action: str = Form(...), db: Session = Depends(get_db)):
    member = db.query(models.Member).get(member_id)
    if member:
        if action == 'approve':
            member.is_approved = True
            db.commit()
        elif action == 'reject':
            db.delete(member)
            db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

# Announcements
@app.get("/admin/announcements", response_class=HTMLResponse, name="manage_announcements")
def manage_announcements(request: Request, db: Session = Depends(get_db)):
    announcements = db.query(models.Announcement).order_by(models.Announcement.created_at.desc()).all()
    return templates.TemplateResponse("admin.html", {"request": request, "announcements": announcements})

@app.post("/admin/announcements")
def add_announcement(request: Request, message: str = Form(...), db: Session = Depends(get_db)):
    announcement = models.Announcement(message=message)
    db.add(announcement)
    db.commit()
    return RedirectResponse(url="/admin/announcements", status_code=status.HTTP_303_SEE_OTHER)

# Register
@app.get("/register", response_class=HTMLResponse, name="register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_member(request: Request, db: Session = Depends(SessionLocal)):
    data = await request.json()
    new_member = models.Member(
        name=data.get("applicantName"),
        dob=data.get("dateOfBirth"),
        designation=data.get("designation"),
        office_tel=data.get("officeTel"),
        mobile=data.get("mobile"),
        bank_account=data.get("bankAccount"),
        aadhaar=data.get("aadhaar"),
        pan=data.get("pan"),
        nominee_name=data.get("nomineeName"),
        nominee_age=data.get("nomineeAge"),
        relationship=data.get("relationship"),
        other_society=data.get("otherSociety"),
        fee_receipt=data.get("feeReceipt"),
        other_details=data.get("otherDetails"),
        application_date=data.get("applicationDate")
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return JSONResponse({"status": "success", "member_id": new_member.id})

# Add member (admin)
@app.get("/admin/add-member", response_class=HTMLResponse, name="admin_add_member")
def admin_add_member_form(request: Request):
    return templates.TemplateResponse("admin_add_member.html", {"request": request})

@app.post("/admin/add-member")
def admin_add_member(request: Request, name: str = Form(...), account_no: str = Form(...), email: str = Form(...), phone: str = Form(...), address: str = Form(...), dob: str = Form(...), gender: str = Form(...), balance: float = Form(0.0), db: Session = Depends(get_db)):
    username = account_no
    password = f"Society{random.randint(1000,9999)}"
    existing_member = db.query(models.Member).filter((models.Member.account_no == account_no) | (models.Member.username == username)).first()
    if existing_member:
        return templates.TemplateResponse("admin_add_member.html", {"request": request, "error": "Account number or username already exists."})
    new_member = models.Member(
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
    db.add(new_member)
    db.commit()
    sms_message = f"Welcome to Society Bank! Your Username: {username}, Password: {password}. Please use these to log in."
    send_sms_fast2sms(phone, sms_message)
    return RedirectResponse(url="/members", status_code=status.HTTP_303_SEE_OTHER)

# Member dashboard
@app.get("/member-dashboard", response_class=HTMLResponse, name="member_dashboard")
def member_dashboard(request: Request, db: Session = Depends(get_db)):
    member_id = request.cookies.get("member_id")
    member = db.query(models.Member).get(member_id)
    account = db.query(models.Account).filter_by(member_id=member_id).first() if member else None
    transactions = db.query(models.Transaction).filter_by(account_id=account.id).all() if account else []
    loans = db.query(models.Loan).filter_by(member_id=member_id).all() if member else []
    shares = []  # Replace with actual query if available
    return templates.TemplateResponse("member_dashboard.html", {"request": request, "member": member, "transactions": transactions, "loans": loans, "shares": shares})

# List members
@app.get("/members", response_class=HTMLResponse, name="list_members")
def list_members(request: Request, db: Session = Depends(get_db)):
    members = db.query(models.Member).all()
    member_details = []
    for member in members:
        loans = db.query(models.Loan).filter_by(member_id=member.id).all()
        account = db.query(models.Account).filter_by(member_id=member.id).first()
        transactions = db.query(models.Transaction).filter_by(account_id=account.id).all() if account else []
        fixed_deposits = db.query(models.Deposit).filter_by(member_id=member.id).all()
        member_details.append({
            'member': member,
            'loans': loans,
            'transactions': transactions,
            'fixed_deposits': fixed_deposits
        })
    return templates.TemplateResponse("list_members.html", {"request": request, "member_details": member_details})

# List accounts
@app.get("/accounts", response_class=HTMLResponse, name="list_accounts")
def list_accounts(request: Request, db: Session = Depends(get_db)):
    accounts = db.query(models.Account).all()
    return templates.TemplateResponse("accounts.html", {"request": request, "accounts": accounts})

# List loans
@app.get("/loans", response_class=HTMLResponse, name="list_loans")
def list_loans(request: Request, db: Session = Depends(get_db)):
    loans = db.query(models.Loan).all()
    return templates.TemplateResponse("loans.html", {"request": request, "loans": loans})

# List deposits
@app.get("/deposits", response_class=HTMLResponse, name="list_deposits")
def list_deposits(request: Request, db: Session = Depends(get_db)):
    deposits = db.query(models.Deposit).all()
    return templates.TemplateResponse("deposits.html", {"request": request, "deposits": deposits})

# List transactions
@app.get("/transactions", response_class=HTMLResponse, name="list_transactions")
def list_transactions(request: Request, db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).all()
    return templates.TemplateResponse("transactions.html", {"request": request, "transactions": transactions})

# Loan application
@app.get("/loan-application", response_class=HTMLResponse)
def loan_application_form(request: Request):
    return templates.TemplateResponse("loan_application.html", {"request": request})

# You can add more endpoints as needed for your banking features.

# Run with: uvicorn main:app --reload