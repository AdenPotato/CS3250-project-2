"""Seed accounts and sample listings, so the app can be graded without manual data entry.
Runs before the server starts (see the Dockerfile) and is idempotent: existing accounts are left
alone, and a vendor's sample listings are added only while that vendor has no listings."""
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models import DietaryTag, Listing, Role, User

# one password for every seed account - listed in the README, so it is not a secret
SEED_PASSWORD = "campuseats123"

ACCOUNTS = (
    ("Campus Deli", "vendor@campuseats.test", Role.VENDOR),
    ("Union Bakery", "bakery@campuseats.test", Role.VENDOR),
    ("Sam Student", "student@campuseats.test", Role.STUDENT),
    ("Riley Student", "student2@campuseats.test", Role.STUDENT),
)

# (vendor email, title, description, portions, location, tags, hours from now to start, window length in hours)
LISTINGS = (
    ("vendor@campuseats.test", "Veggie wraps", "Hummus and roasted vegetable wraps left from lunch.",
     12, "Student Union", ("vegetarian",), 0, 4),
    ("vendor@campuseats.test", "Chicken shawarma bowls", "Rice bowls with halal chicken and garlic sauce.",
     8, "Main Dining Hall", ("halal", "gluten-free"), 1, 6),
    ("vendor@campuseats.test", "Fruit cups", "Fresh cut melon, grapes and berries.",
     20, "Library Cafe", ("vegan", "gluten-free"), 0, 48),
    ("bakery@campuseats.test", "Day-old bagels", "Plain and sesame bagels, still soft.",
     30, "Student Union", ("vegan",), 2, 24),
    ("bakery@campuseats.test", "Almond croissants", "Butter croissants with almond filling.",
     6, "Science Building", ("vegetarian", "contains nuts"), 0, 72),
)


def seed():
    users = {}
    for name, email, role in ACCOUNTS:
        user = db.session.scalar(db.select(User).filter_by(email=email))
        if user is None:
            user = User(name=name, email=email, role=role)
            user.set_password(SEED_PASSWORD)
            db.session.add(user)
        users[email] = user
    db.session.flush()

    # checked before adding any, so a vendor with listings from an earlier start gets no duplicates
    stocked = {email for email, user in users.items() if user.listings}
    tags = {t.name: t for t in db.session.scalars(db.select(DietaryTag))}
    # windows start relative to the first start, so a fresh volume always shows open listings
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for email, title, description, portions, location, tag_names, start_in, length in LISTINGS:
        if email in stocked:
            continue
        start = now + timedelta(hours=start_in)
        db.session.add(Listing(
            vendor=users[email],
            title=title,
            description=description,
            portions=portions,
            portions_remaining=portions,
            location=location,
            pickup_start=start,
            pickup_end=start + timedelta(hours=length),
            tags=[tags[n] for n in tag_names],
        ))

    db.session.commit()


if __name__ == "__main__":
    with create_app().app_context():
        seed()
    print("seed data ready")
