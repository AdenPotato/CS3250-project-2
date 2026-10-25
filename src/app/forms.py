from flask_wtf import FlaskForm
from wtforms import PasswordField, RadioField, StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError

from . import db
from .models import Role, User


def _normalize_email(value):
    # "Ana@x.edu " and "ana@x.edu" are the same account, so the duplicate check sees them as one
    return value.strip().lower() if value else value


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired("Enter your name."), Length(max=100)])
    email = StringField(
        "Email",
        filters=[_normalize_email],
        validators=[DataRequired("Enter your email."), Length(max=255)],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired("Enter a password."),
            Length(min=8, message="Password must be at least 8 characters."),
        ],
    )
    role = RadioField(
        "I am a",
        choices=[(Role.STUDENT.value, "Student"), (Role.VENDOR.value, "Vendor")],
        validators=[InputRequired("Choose Student or Vendor.")],
    )
    submit = SubmitField("Register")

    def validate_email(self, field):
        if db.session.scalar(db.select(User).filter_by(email=field.data)):
            raise ValidationError("That email is already registered.")


class LoginForm(FlaskForm):
    email = StringField("Email", filters=[_normalize_email], validators=[DataRequired("Enter your email.")])
    password = PasswordField("Password", validators=[DataRequired("Enter your password.")])
    submit = SubmitField("Log in")
