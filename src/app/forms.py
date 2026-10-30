from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, RadioField, SelectMultipleField, StringField, SubmitField, TextAreaField, DateTimeLocalField, widgets
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, ValidationError

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


class ListingForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired("Enter a title."), Length(max=150)])
    description = TextAreaField("Description", validators=[DataRequired("Enter a description.")])
    portions = IntegerField(
        "Portions Available",
        validators=[
            DataRequired("Enter number of portions."),
            NumberRange(min=1, max=100, message="Portions must be between 1 and 100."),
        ],
    )
    location = StringField("Pickup Location", validators=[DataRequired("Enter a pickup location.")])
    dietary_tags = SelectMultipleField(
        "Dietary Tags",
        choices=[
            ("vegetarian", "Vegetarian"),
            ("vegan", "Vegan"),
            ("gluten-free", "Gluten-Free"),
            ("halal", "Halal"),
            ("contains nuts", "Contains Nuts"),
        ],
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput()
    )
    window_start = DateTimeLocalField(
        "Pickup Window Start", format="%Y-%m-%dT%H:%M", validators=[DataRequired("Enter pickup start time.")]
    )
    window_end = DateTimeLocalField(
        "Pickup Window End", format="%Y-%m-%dT%H:%M", validators=[DataRequired("Enter pickup end time.")]
    )
    submit = SubmitField("Post Listing")

    def validate_window_start(self, field):
        if field.data and field.data < datetime.now():
            raise ValidationError("Pickup window start cannot be in the past.")

    def validate_window_end(self, field):
        if field.data and field.data < datetime.now():
            raise ValidationError("Pickup window end cannot be in the past.")
        if field.data and self.window_start.data and field.data <= self.window_start.data:
            raise ValidationError("Pickup window end must be after the start time.")


class ReserveForm(FlaskForm):
    portions = RadioField(
        "Portions",
        choices=[("1", "1 portion"), ("2", "2 portions")],
        validators=[InputRequired("Select how many portions to reserve.")],
    )
    submit = SubmitField("Reserve")


class PickupCodeForm(FlaskForm):
    pickup_code = StringField("Pickup Code", validators=[DataRequired("Enter the pickup code.")])
    submit = SubmitField("Confirm Pickup")