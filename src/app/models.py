# User, Listing, Reservation and DietaryTag land here - see uml/class.wsd.
from . import db, login_manager  # noqa: F401


@login_manager.user_loader
def load_user(user_id):
    # placeholder so templates can render current_user - US1 replaces it with
    # db.session.get(User, int(user_id))
    return None
