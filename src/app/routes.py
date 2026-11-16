from datetime import datetime, time, timedelta, timezone
from functools import wraps

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFError
from sqlalchemy.exc import IntegrityError

from . import db
from .campus_time import campus_to_utc, to_campus
from .forms import DashboardForm, ListingFilterForm, ListingForm, LoginForm, PickupCodeForm, RatingForm, RegisterForm, ReserveForm
from .models import CAMPUS_LOCATIONS, DIETARY_TAGS, DietaryTag, Listing, Rating, Reservation, ReservationStatus, Role, User, mark_no_shows

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


@bp.app_errorhandler(CSRFError)
def csrf_failed(error):
    # CSRFProtect rejects the POST before the view runs. Running the view now is safe: its
    # form fails the same token check, so it only re-renders with a fresh token, or redirects
    if request.endpoint not in ("main.register", "main.login"):
        return error
    flash("Your session expired - please try again.", "error")
    return current_app.view_functions[request.endpoint]()


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    return render_template("index.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
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


def impact_stats(vendor_id, start_utc, end_utc):
    # US9.1: listings posted in [start, end) by creation date, and what happened to their portions.
    # cancelled reservations were given back, so they do not count as reserved (US9.2)
    posted = db.select(Listing.id).where(
        Listing.vendor_id == vendor_id, Listing.creation_date >= start_utc, Listing.creation_date < end_utc
    )
    listings_posted, portions_posted = db.session.execute(
        db.select(db.func.count(Listing.id), db.func.coalesce(db.func.sum(Listing.portions), 0)).where(
            Listing.id.in_(posted)
        )
    ).one()

    def portions_with(*statuses):
        return db.session.scalar(
            db.select(db.func.coalesce(db.func.sum(Reservation.portions), 0)).where(
                Reservation.listing_id.in_(posted), Reservation.status.in_(statuses)
            )
        )

    no_shows = db.session.scalar(
        db.select(db.func.count(Reservation.id)).where(
            Reservation.listing_id.in_(posted), Reservation.status == ReservationStatus.NO_SHOW
        )
    )
    reserved = portions_with(ReservationStatus.ACTIVE, ReservationStatus.PICKED_UP, ReservationStatus.NO_SHOW)
    no_show_portions = portions_with(ReservationStatus.NO_SHOW)
    return {
        "listings_posted": listings_posted,
        "portions_posted": portions_posted,
        "portions_reserved": reserved,
        "portions_picked_up": portions_with(ReservationStatus.PICKED_UP),
        "no_shows": no_shows,
        "no_show_portions": no_show_portions,
        # US9.3: an empty range has nothing reserved, so the rate is 0, not a division by zero
        "no_show_rate": round(100 * no_show_portions / reserved, 1) if reserved else 0,
    }


@bp.route("/vendor/dashboard")
@role_required(Role.VENDOR)
def dashboard():
    mark_no_shows()
    form = DashboardForm(request.args)
    today = to_campus(datetime.now(timezone.utc)).date()
    if not request.args:
        # the last 30 days by default, so the page shows something before a range is chosen
        form.start.data, form.end.data = today - timedelta(days=29), today
    stats = None
    if not request.args or form.validate():
        # the dates are campus days, so the range runs from campus midnight to the next midnight
        start_utc = campus_to_utc(datetime.combine(form.start.data, time.min))
        end_utc = campus_to_utc(datetime.combine(form.end.data + timedelta(days=1), time.min))
        stats = impact_stats(current_user.id, start_utc, end_utc)
    return render_template("vendor/dashboard.html", title="Impact Dashboard", form=form, stats=stats)


def rating_summary(listing_ids):
    # US10.3: {listing id: (average stars, number of ratings)} for listings with at least one rating
    rows = db.session.execute(
        db.select(Reservation.listing_id, db.func.avg(Rating.stars), db.func.count(Rating.id))
        .join(Rating, Rating.reservation_id == Reservation.id)
        .where(Reservation.listing_id.in_(listing_ids))
        .group_by(Reservation.listing_id)
    ).all()
    return {listing_id: (round(float(avg), 1), n) for listing_id, avg, n in rows}


@bp.route("/vendor/listings")
@role_required(Role.VENDOR)
def my_listings():
    listings = db.session.scalars(
        db.select(Listing).where(Listing.vendor_id == current_user.id).order_by(Listing.creation_date.desc())
    ).all()
    now = datetime.now(timezone.utc)
    return render_template(
        "vendor/my_listings.html", title="My Listings", listings=listings, now=now,
        ratings=rating_summary([l.id for l in listings]),
    )


@bp.route("/vendor/listings/<int:listing_id>/edit", methods=["GET", "POST"])
@role_required(Role.VENDOR)
def edit_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if not listing or listing.vendor_id != current_user.id:
        abort(404)
    form = ListingForm(obj=listing)
    form.current_start = listing.pickup_start
    if request.method == 'GET':
        form.window_start.data = listing.pickup_start
        form.window_end.data = listing.pickup_end
        form.dietary_tags.data = [t.name for t in listing.tags]

    if form.validate_on_submit():
        # lock the row as reserve_listing does, so a reservation made during the save is not lost
        db.session.refresh(listing, with_for_update=True)
        # picked-up and no-show portions are gone too, so only cancelled ones are free (US5.3)
        reserved_total = db.session.scalar(
            db.select(db.func.coalesce(db.func.sum(Reservation.portions), 0)).where(
                Reservation.listing_id == listing.id,
                Reservation.status != ReservationStatus.CANCELLED,
            )
        ) or 0

        new_portions = form.portions.data
        if new_portions < reserved_total:
            form.portions.errors.append(
                f"{reserved_total} portions are already reserved, so portions cannot be set below {reserved_total}."
            )
            return render_template("vendor/edit_listing.html", title="Edit Listing", form=form, listing=listing)

        selected_tags = []
        if form.dietary_tags.data:
            selected_tags = list(
                db.session.scalars(
                    db.select(DietaryTag).where(DietaryTag.name.in_(form.dietary_tags.data))
                )
            )

        try:
            listing.title = form.title.data.strip()
            listing.description = form.description.data.strip()
            listing.portions = new_portions
            listing.portions_remaining = new_portions - reserved_total
            listing.location = form.location.data.strip()
            listing.pickup_start = form.window_start.data
            listing.pickup_end = form.window_end.data
            listing.tags = selected_tags
            db.session.commit()
            flash("Listing updated.", "success")
            return redirect(url_for("main.my_listings"))
        except Exception:
            db.session.rollback()
            flash("Could not update listing.", "error")
            return render_template("vendor/edit_listing.html", title="Edit Listing", form=form, listing=listing)

    return render_template("vendor/edit_listing.html", title="Edit Listing", form=form, listing=listing)


@bp.route("/vendor/listings/<int:listing_id>/cancel", methods=["POST"])
@role_required(Role.VENDOR)
def cancel_listing(listing_id):
    listing = db.session.get(Listing, listing_id)
    if not listing or listing.vendor_id != current_user.id:
        abort(404)
    try:
        listing.cancelled = True
        active_reservations = db.session.scalars(
            db.select(Reservation).where(
                Reservation.listing_id == listing.id,
                Reservation.status == ReservationStatus.ACTIVE,
            )
        ).all()
        for r in active_reservations:
            r.status = ReservationStatus.CANCELLED
        db.session.commit()
        flash("Listing cancelled. Active reservations cancelled.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not cancel listing.", "error")
    return redirect(url_for("main.my_listings"))


@bp.route("/vendor/listings/<int:listing_id>")
@role_required(Role.VENDOR)
def view_listing_reservations(listing_id):
    listing = db.session.get(Listing, listing_id)
    if not listing or listing.vendor_id != current_user.id:
        abort(404)
    mark_no_shows()
    reservations = db.session.scalars(
        db.select(Reservation).where(Reservation.listing_id == listing.id).order_by(Reservation.created_at.desc())
    ).all()
    rated = [r for r in reservations if r.rating]
    return render_template(
        "vendor/listing_detail.html", title="Listing Details", listing=listing, reservations=reservations,
        rating=rating_summary([listing.id]).get(listing.id), rated=rated,
    )


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


@bp.route("/listings")
@role_required(Role.STUDENT)
def listings():
    form = ListingFilterForm(formdata=request.args)
    # unknown values from a hand-edited URL are ignored rather than shown as errors
    tags = [t for t in form.tags.data or [] if t in DIETARY_TAGS]
    location = form.location.data if form.location.data in CAMPUS_LOCATIONS else None

    query = (
        db.select(Listing)
        .where(Listing.cancelled.is_(False))
        .where(Listing.pickup_end > datetime.now(timezone.utc))
        .where(Listing.portions_remaining > 0)
    )
    # one condition per tag, so a listing must carry every selected tag (US8.1)
    for tag in tags:
        query = query.where(Listing.tags.any(DietaryTag.name == tag))
    if location:
        query = query.where(Listing.location == location)
    listings = db.session.scalars(query.order_by(Listing.pickup_end.asc())).all()
    return render_template("listings/index.html", title="Available Listings", listings=listings, form=form)


@bp.route("/reservations")
@role_required(Role.STUDENT)
def my_reservations():
    mark_no_shows()
    now = datetime.now(timezone.utc)
    reservations = db.session.scalars(
        db.select(Reservation)
        .where(Reservation.user_id == current_user.id)
        .order_by(Reservation.created_at.desc())
    ).all()
    return render_template("reservations/index.html", title="My Reservations", reservations=reservations, now=now)


@bp.route("/reservations/<int:reservation_id>/cancel", methods=["POST"])
@role_required(Role.STUDENT)
def cancel_reservation(reservation_id):
    mark_no_shows()
    reservation = db.session.execute(
        db.select(Reservation)
        .where(Reservation.id == reservation_id)
        .where(Reservation.user_id == current_user.id)
        .with_for_update()
    ).scalar_one_or_none()
    if not reservation:
        abort(404)

    try:
        if reservation.status != ReservationStatus.ACTIVE:
            db.session.rollback()
            flash("This reservation cannot be cancelled.", "error")
            return redirect(url_for("main.my_reservations"))
        listing = db.session.execute(
            db.select(Listing).where(Listing.id == reservation.listing_id).with_for_update()
        ).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if not listing or listing.pickup_end <= now or listing.cancelled:
            db.session.rollback()
            flash("This reservation cannot be cancelled.", "error")
            return redirect(url_for("main.my_reservations"))

        reservation.status = ReservationStatus.CANCELLED
        listing.portions_remaining += reservation.portions
        db.session.commit()
        flash("Reservation cancelled. Portions returned.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not cancel reservation.", "error")
    return redirect(url_for("main.my_reservations"))


@bp.route("/reservations/<int:reservation_id>/rate", methods=["GET", "POST"])
@role_required(Role.STUDENT)
def rate_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation or reservation.user_id != current_user.id:
        abort(404)
    # US10.2: only a picked-up reservation, and only once
    if reservation.rating:
        flash("You have already rated this pickup.", "error")
        return redirect(url_for("main.my_reservations"))
    if reservation.status != ReservationStatus.PICKED_UP:
        flash("Only picked-up reservations can be rated.", "error")
        return redirect(url_for("main.my_reservations"))

    form = RatingForm()
    if form.validate_on_submit():
        db.session.add(Rating(reservation_id=reservation.id, stars=form.stars.data, comment=form.comment.data or None))
        try:
            db.session.commit()
        except IntegrityError:
            # a second tab submitted first; the unique reservation_id kept it to one rating
            db.session.rollback()
            flash("You have already rated this pickup.", "error")
            return redirect(url_for("main.my_reservations"))
        flash("Thanks! Your rating was submitted.", "success")
        return redirect(url_for("main.my_reservations"))
    return render_template("reservations/rate.html", title="Rate Pickup", form=form, reservation=reservation)


@bp.route("/listings/<int:listing_id>/reserve", methods=["GET", "POST"])
@role_required(Role.STUDENT)
def reserve_listing(listing_id):
    listing = db.session.execute(
        db.select(Listing)
        .where(Listing.id == listing_id)
        .where(Listing.cancelled.is_(False))
        .where(Listing.pickup_end > datetime.now(timezone.utc))
        .with_for_update()
    ).scalar_one_or_none()
    if not listing:
        abort(404)

    form = ReserveForm()
    if form.validate_on_submit():
        portions_to_reserve = form.portions.data
        already_reserved = db.session.execute(
            db.select(Reservation)
            .where(Reservation.user_id == current_user.id)
            .where(Reservation.listing_id == listing.id)
            .where(Reservation.status == ReservationStatus.ACTIVE)
        ).scalar_one_or_none()
        if already_reserved:
            flash("You already have a reservation for this listing.", "error")
            return render_template("listings/reserve.html", title="Reserve Listing", form=form, listing=listing)
        if portions_to_reserve > listing.portions_remaining:
            flash("Not enough portions available.", "error")
            return render_template("listings/reserve.html", title="Reserve Listing", form=form, listing=listing)

        reservation = Reservation(
            user_id=current_user.id,
            listing_id=listing.id,
            portions=portions_to_reserve,
            pickup_code=Reservation.generate_pickup_code(),
            status=ReservationStatus.ACTIVE,
        )
        listing.portions_remaining -= portions_to_reserve
        db.session.add(reservation)
        db.session.commit()
        flash(f"Reserved! Your pickup code is {reservation.pickup_code}", "success")
        return redirect(url_for("main.my_reservations"))

    return render_template("listings/reserve.html", title="Reserve Listing", form=form, listing=listing)


@bp.route("/vendor/confirm-pickup", methods=["GET", "POST"])
@role_required(Role.VENDOR)
def confirm_pickup():
    mark_no_shows()
    now = datetime.now(timezone.utc)

    form = PickupCodeForm()
    if form.validate_on_submit():
        code = form.pickup_code.data.strip().upper()
        reservation = db.session.scalar(db.select(Reservation).where(Reservation.pickup_code == code))
        if not reservation:
            flash("Invalid pickup code.", "error")
            return render_template("vendor/confirm_pickup.html", title="Confirm Pickup", form=form)
        listing = reservation.listing
        if listing.vendor_id != current_user.id:
            flash("This pickup code does not belong to one of your listings.", "error")
            return render_template("vendor/confirm_pickup.html", title="Confirm Pickup", form=form)
        if reservation.status == ReservationStatus.NO_SHOW:
            flash("This reservation has expired and is marked as no-show.", "error")
            return render_template("vendor/confirm_pickup.html", title="Confirm Pickup", form=form)
        if reservation.status != ReservationStatus.ACTIVE:
            flash("This reservation has already been used or cancelled.", "error")
            return render_template("vendor/confirm_pickup.html", title="Confirm Pickup", form=form)
        if listing.pickup_end <= now:
            reservation.status = ReservationStatus.NO_SHOW
            db.session.commit()
            flash("This reservation has expired and is marked as no-show.", "error")
            return render_template("vendor/confirm_pickup.html", title="Confirm Pickup", form=form)
        try:
            reservation.status = ReservationStatus.PICKED_UP
            db.session.commit()
            flash(f"Pickup confirmed for {reservation.student.name} ({reservation.portions} portion(s)).", "success")
            return render_template("vendor/confirm_pickup.html", title="Confirm Pickup", form=form)
        except Exception:
            db.session.rollback()
            flash("Could not confirm pickup.", "error")
            return render_template("vendor/confirm_pickup.html", title="Confirm Pickup", form=form)

    return render_template("vendor/confirm_pickup.html", title="Confirm Pickup", form=form)
