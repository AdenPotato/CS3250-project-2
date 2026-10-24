# User, Listing, Reservation and DietaryTag land here - see uml/class.wsd.
import enum
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager


class Role(enum.Enum):
    STUDENT = "student"
    VENDOR = "vendor"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # unique in the database so a duplicate email fails even if the form check is skipped (US1.2)
    email = db.Column(db.String(255), unique=True, nullable=False)
    # only the werkzeug hash is stored, never the password itself (US1.4)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(Role, name="user_role", values_callable=lambda r: [m.value for m in r]),
        nullable=False,
    )
    active = db.Column(db.Boolean, nullable=False, default=True)
    creation_date = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        # Flask-Login refuses to log in a user whose is_active is False
        return self.active

    @property
    def is_vendor(self):
        return self.role is Role.VENDOR

    @property
    def is_student(self):
        return self.role is Role.STUDENT


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
