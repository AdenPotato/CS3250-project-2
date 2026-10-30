import enum
import secrets
import string
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager


class Role(enum.Enum):
    STUDENT = "student"
    VENDOR = "vendor"


class ReservationStatus(enum.Enum):
    ACTIVE = "active"
    PICKED_UP = "picked up"
    CANCELLED = "cancelled"
    NO_SHOW = "no-show"


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

    # a vendor's listings; students have none
    listings = db.relationship("Listing", back_populates="vendor", order_by="Listing.pickup_end")
    reservations = db.relationship("Reservation", back_populates="student", order_by="Reservation.id")

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


# placeholder campus locations - a fixed list so US8 can filter by exact match; edit to match campus
CAMPUS_LOCATIONS = (
    "Student Union",
    "Main Dining Hall",
    "Library Cafe",
    "Science Building",
    "Recreation Center",
)

# the five tags US2.1 names, created on startup by ensure_dietary_tags
DIETARY_TAGS = ("vegetarian", "vegan", "gluten-free", "halal", "contains nuts")

listing_tags = db.Table(
    "listing_tags",
    db.Column("listing_id", db.ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.ForeignKey("dietary_tags.id"), primary_key=True),
)


class DietaryTag(db.Model):
    __tablename__ = "dietary_tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Listing(db.Model):
    __tablename__ = "listings"
    # enforced by PostgreSQL too, so a buggy route cannot store a bad listing (US2.1, US2.2, US4.4)
    __table_args__ = (
        db.CheckConstraint("portions BETWEEN 1 AND 100", name="portions_range"),
        db.CheckConstraint(
            "portions_remaining BETWEEN 0 AND portions", name="portions_remaining_range"
        ),
        db.CheckConstraint("pickup_end > pickup_start", name="pickup_window_order"),
    )

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    portions = db.Column(db.Integer, nullable=False)
    portions_remaining = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    pickup_start = db.Column(db.DateTime(timezone=True), nullable=False)
    pickup_end = db.Column(db.DateTime(timezone=True), nullable=False)
    cancelled = db.Column(db.Boolean, nullable=False, default=False)
    creation_date = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    vendor = db.relationship("User", back_populates="listings")
    tags = db.relationship("DietaryTag", secondary=listing_tags, order_by="DietaryTag.name")
    reservations = db.relationship("Reservation", back_populates="listing", order_by="Reservation.id")


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey("users.id"), nullable=False, index=True)
    listing_id = db.Column(db.ForeignKey("listings.id"), nullable=False, index=True)
    portions = db.Column(db.Integer, nullable=False)
    pickup_code = db.Column(db.String(6), unique=True, nullable=False)
    status = db.Column(
        db.Enum(
            ReservationStatus,
            name="reservation_status",
            values_callable=lambda r: [m.value for m in r],
        ),
        nullable=False,
        default=ReservationStatus.ACTIVE,
    )
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    student = db.relationship("User", back_populates="reservations")
    listing = db.relationship("Listing", back_populates="reservations")

    @staticmethod
    def generate_pickup_code():
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(6))
            if not db.session.scalar(db.select(Reservation).filter_by(pickup_code=code)):
                return code


def ensure_dietary_tags():
    # idempotent, so every restart is safe and a fresh volume always has the five tags
    existing = set(db.session.scalars(db.select(DietaryTag.name)))
    db.session.add_all(DietaryTag(name=n) for n in DIETARY_TAGS if n not in existing)
    db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))