from datetime import timezone
from zoneinfo import ZoneInfo

# vendors type pickup windows on the campus wall clock; the database stores UTC (#95)
CAMPUS_TZ = ZoneInfo("America/Denver")


def campus_to_utc(naive):
    """A wall-clock time typed on campus, as an aware UTC datetime."""
    return naive.replace(tzinfo=CAMPUS_TZ).astimezone(timezone.utc)


def to_campus(aware):
    """A stored UTC datetime, as campus local time."""
    return aware.astimezone(CAMPUS_TZ)


def format_campus(aware, fmt="%m/%d/%Y %I:%M %p"):
    """Jinja filter `campus` - show a stored time on the campus clock."""
    return to_campus(aware).strftime(fmt) if aware else ""
