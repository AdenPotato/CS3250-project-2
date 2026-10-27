from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from . import db
from .forms import ListingForm, LoginForm, RegisterForm
from .models import DietaryTag, Listing, Role, User

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


@bp.route("/listings/new", methods=["GET", "POST"])
@role_required(Role.VENDOR)
def new_listing():
    form = ListingForm()
    if form.validate_on_submit():
        # Fetch the DietaryTag instances matching selected checkbox values
        selected_tags = []
        if form.dietary_tags.data:
            selected_tags = list(
                db.session.scalars(
                    db.select(DietaryTag).where(DietaryTag.name.in_(form.dietary_tags.data))
                )
            )

        listing = Listing(
            vendor_id=current_user.id,
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            portions=form.portions.data,
            portions_remaining=form.portions.data,  # Satisfies portions_remaining_range constraint
            location=form.location.data.strip(),
            pickup_start=form.window_start.data,
            pickup_end=form.window_end.data,
            tags=selected_tags,  # Matches the 'tags' relationship in models.py
        )
        db.session.add(listing)
        db.session.commit()
        flash("Surplus food listing posted successfully.", "success")
        return redirect(url_for("main.vendor_home"))

    return render_template("listings/new.html", title="New Listing", form=form)