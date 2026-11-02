import re
from wtforms.validators import ValidationError

MIN_LENGTH = 8

#Return a list of the rules this password breaks (empty list = strong enough).
def password_problems(password):
    
    problems = []

    if len(password) < MIN_LENGTH:
        problems.append(f"at least {MIN_LENGTH} characters")
    if not re.search(r"[A-Z]", password):
        problems.append("an uppercase letter")
    if not re.search(r"[a-z]", password):
        problems.append("a lowercase letter")
    if not re.search(r"\d", password):
        problems.append("a number")
    if not re.search(r"[^A-Za-z0-9\s]", password):
        problems.append("a symbol")

    return problems

# WTForms validator: use it in a field's validators=[...] list.
def strong_password(form, field):

    problems = password_problems(field.data or "")
    if problems:
        raise ValidationError("Password needs " + ", ".join(problems) + ".")