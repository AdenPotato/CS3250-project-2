from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from sqlalchemy.exc import IntegrityError

from . import db
from .forms import RegisterForm
from .models import Role, User

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
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
        # login arrives in #12; until then land on the home page
        target = "main.login" if "main.login" in current_app.view_functions else "main.index"
        return redirect(url_for(target))
    return render_template("register.html", title="Register", form=form)
