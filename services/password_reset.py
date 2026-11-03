import hashlib
import logging
import os
import smtplib
from email.message import EmailMessage

from flask import current_app
from itsdangerous import BadSignature, URLSafeTimedSerializer

from models import db, Student

logger = logging.getLogger(__name__)

RESET_SALT = "password-reset"
RESET_MAX_AGE = 3600

def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=RESET_SALT)

#Short fingerprint of the current password hash.
def _fingerprint(student):
    return hashlib.sha256(student.password_hash.encode()).hexdigest()[:16]

def generate_reset_token(student):
    return _serializer().dumps({"id": student.id, 
                                "fp": _fingerprint(student)})
    
#Return the Student the token belongs to, or None if it is invalid/expired/used.
def verify_reset_token(token, max_age=RESET_MAX_AGE):
    
    try:
        data = _serializer().loads(token, max_age=max_age)
    except BadSignature:
        return None
    
    student = db.session.get(Student, data["id"])
    if student is None or data["fp"] != _fingerprint(student):
        return None
    return student

#Email the reset link. Without SMTP settings, log it instead (development).
def send_reset_email(to_address, link):

    host = os.environ.get("SMTP_HOST")
    if not host:
        logger.warning("SMTP not configured. Reset link for %s: %s", to_address, link)
        return
 
    message = EmailMessage()
    message["Subject"] = "Reset your GradePulse password"
    message["From"] = os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", ""))
    message["To"] = to_address
    message.set_content(
        "Use this link to choose a new password (valid for 1 hour):\n\n"
        f"{link}\n\n"
        "If you didn't ask for this, you can ignore this email."
    )
 
    try:
        with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
            server.send_message(message)
    except Exception:
        logger.exception("Could not send password reset email")
    