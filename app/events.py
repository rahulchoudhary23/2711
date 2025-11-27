from flask import Blueprint
from flask_login import login_required
from .models import Event

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/")
def home():
    return "Events homepage is LIVE!"


@events_bp.route("/list")
def list_events():
    events = Event.query.all()
    output = [e.title for e in events]
    return {"events": output}

