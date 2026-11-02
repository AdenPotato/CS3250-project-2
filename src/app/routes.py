from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from . import db
from .forms import LoginForm, RegisterForm
from .models import Role, User, Reservation, Listing

bp = Blueprint("main", __name__)


def role_required(role):
    # login_required proves who the user is; this proves they may be here (e.g. US2.3)
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role is not role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def _home_for(user):
    return url_for("main.vendor_home" if user.is_vendor else "main.student_home")


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    return render_template("index.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data.strip(), email=form.email.data, role=Role(form.role.data))
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            # two submits with the same email at once - the unique constraint catches the second
            db.session.rollback()
            form.email.errors.append("That email is already registered.")
            return render_template("register.html", title="Register", form=form)
        flash("Account created - log in to continue.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html", title="Register", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).filter_by(email=form.email.data))
        # one message for unknown email and wrong password, so it does not reveal which accounts exist
        if user and user.check_password(form.password.data) and login_user(user):
            return redirect(_home_for(user))
        flash("Incorrect email or password.", "error")
    return render_template("login.html", title="Log in", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))


@bp.route("/student")
@role_required(Role.STUDENT)
def student_home():
    return render_template("student_home.html", title="Home")


@bp.route("/vendor")
@role_required(Role.VENDOR)
def vendor_home():
    return render_template("vendor_home.html", title="Home")
@bp.route("/listings/<int:id>/reserve", methods=["POST"])
@role_required(Role.STUDENT)
def reserve_listing(id):
    # 1. Parse and validate requested portions (AC 4.1: Reserve 1 or 2 portions)
    try:
        portions_requested = int(request.form.get("portions", 1))
    except (TypeError, ValueError):
        flash("Invalid portion quantity.", "danger")
        return redirect(url_for("main.student_home"))

    if portions_requested not in (1, 2):
        flash("You can only reserve 1 or 2 portions at a time.", "danger")
        return redirect(url_for("main.student_home"))

    # 2. Reject a second active reservation for this user (AC 4.3)
    existing_active = db.session.scalar(
        db.select(Reservation).filter_by(user_id=current_user.id, status="active")
    )
    if existing_active:
        flash("You already have an active reservation.", "warning")
        return redirect(url_for("main.student_home"))

    # 3. Lock the listing row using SELECT ... FOR UPDATE (AC 4.4)
    listing = db.session.query(Listing).filter_by(id=id).with_for_update().first()

    if not listing or listing.cancelled:
        flash("Listing not found or no longer available.", "danger")
        return redirect(url_for("main.student_home"))

    # 4. Reject if requested portions exceed remaining portions (AC 4.2)
    if portions_requested > listing.portions_remaining:
        flash(f"Cannot reserve {portions_requested} portions. Only {listing.portions_remaining} remaining.", "danger")
        return redirect(url_for("main.student_home"))

    # 5. Deduct portions and create active reservation (AC 4.1)
    listing.portions_remaining -= portions_requested
    reservation = Reservation(
        user_id=current_user.id,
        listing_id=listing.id,
        portions_reserved=portions_requested,
        status="active"
    )

    db.session.add(reservation)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("An error occurred while processing your reservation. Please try again.", "danger")
        return redirect(url_for("main.student_home"))

    flash(f"Successfully reserved {portions_requested} portion(s)!", "success")
    return redirect(url_for("main.student_home"))