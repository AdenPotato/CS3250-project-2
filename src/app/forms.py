from datetime import datetime, timezone
from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, RadioField, SelectField, SelectMultipleField, StringField, SubmitField, TextAreaField, DateTimeLocalField, widgets
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, StopValidation, ValidationError

from . import db
from .campus_time import campus_to_utc, to_campus
from .models import CAMPUS_LOCATIONS, DIETARY_TAGS, Role, User


def _normalize_email(value):
    # "Ana@x.edu " and "ana@x.edu" are the same account, so the duplicate check sees them as one
    return value.strip().lower() if value else value


def _no_nul(form, field):
    # postgres text cannot hold a NUL, so psycopg would raise and the page would be a 500.
    # StopValidation, not ValidationError, so validate_email never queries with this value
    if field.data and "\x00" in field.data:
        raise StopValidation("This field contains an invalid character.")


class CampusDateTimeField(DateTimeLocalField):
    # the browser sends campus wall-clock time; data holds it as aware UTC so it is stored
    # and compared at the right instant (#95), and is shown back on the campus clock
    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)
        if self.data is not None:
            self.data = campus_to_utc(self.data)

    def _value(self):
        if self.raw_data:
            return " ".join(self.raw_data)
        return to_campus(self.data).strftime(self.format[0]) if self.data else ""


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[_no_nul, DataRequired("Enter your name."), Length(max=100)])
    email = StringField(
        "Email",
        filters=[_normalize_email],
        validators=[_no_nul, DataRequired("Enter your email."), Length(max=255)],
    )
    password = PasswordField(
        "Password",
        validators=[
            _no_nul,
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
    email = StringField("Email", filters=[_normalize_email], validators=[_no_nul, DataRequired("Enter your email.")])
    password = PasswordField("Password", validators=[_no_nul, DataRequired("Enter your password.")])
    submit = SubmitField("Log in")


class ListingForm(FlaskForm):
    # limits match the String(100) columns in models.py, so a long value is a form error, not a 500
    title = StringField(
        "Title",
        validators=[_no_nul, DataRequired("Enter a title."), Length(max=100, message="Title must be at most 100 characters.")],
    )
    description = TextAreaField("Description", validators=[_no_nul, DataRequired("Enter a description.")])
    portions = IntegerField(
        "Portions Available",
        validators=[
            DataRequired("Enter number of portions."),
            NumberRange(min=1, max=100, message="Portions must be between 1 and 100."),
        ],
    )
    # a fixed campus list, so students can filter by exact location (US8.2); SelectField
    # rejects any value not in the list with "Not a valid choice."
    location = SelectField(
        "Pickup Location",
        choices=[("", "Choose a location")] + [(loc, loc) for loc in CAMPUS_LOCATIONS],
        validators=[DataRequired("Choose a pickup location.")],
    )
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
    window_start = CampusDateTimeField(
        "Pickup Window Start", format="%Y-%m-%dT%H:%M", validators=[DataRequired("Enter pickup start time.")]
    )
    window_end = CampusDateTimeField(
        "Pickup Window End", format="%Y-%m-%dT%H:%M", validators=[DataRequired("Enter pickup end time.")]
    )
    submit = SubmitField("Post Listing")

    # the edit route sets this, so a listing whose window has already opened can still be saved
    # as long as its start is left as it was (US5.2)
    current_start = None

    def validate_window_start(self, field):
        if field.data and self.current_start and field.data == self.current_start.replace(second=0, microsecond=0):
            return
        if field.data and field.data < datetime.now(timezone.utc):
            raise ValidationError("Pickup window start cannot be in the past.")

    def validate_window_end(self, field):
        if field.data and field.data < datetime.now(timezone.utc):
            raise ValidationError("Pickup window end cannot be in the past.")
        if field.data and self.window_start.data and field.data <= self.window_start.data:
            raise ValidationError("Pickup window end must be after the start time.")


class ListingFilterForm(FlaskForm):
    # read from the query string on GET /listings, so filters show in the URL and need no CSRF
    class Meta:
        csrf = False

    tags = SelectMultipleField(
        "Dietary tags",
        choices=[(t, t.title()) for t in DIETARY_TAGS],
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput(),
    )
    location = SelectField(
        "Campus location", choices=[("", "Any location")] + [(loc, loc) for loc in CAMPUS_LOCATIONS]
    )


class ReserveForm(FlaskForm):
    choices = [(1, "1 portion"), (2, "2 portions")]
    portions = RadioField("Portions to Reserve", choices=choices, coerce=int, validators=[InputRequired()])
    submit = SubmitField("Reserve")


class PickupCodeForm(FlaskForm):
    # _no_nul first: the code is looked up in postgres, which rejects a NUL byte with a 500 (US7.2)
    pickup_code = StringField("Pickup Code", validators=[_no_nul, DataRequired("Enter the pickup code.")])
    submit = SubmitField("Confirm Pickup")
