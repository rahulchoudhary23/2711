from datetime import datetime
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models import EVENT_CATEGORY_CHOICES, Event, EventInterest, Registration

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(func):
    """Decorator to ensure the current user has admin privileges."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in as an administrator.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        if not current_user.is_admin:
            flash("Administrator access required.", "danger")
            return redirect(url_for("events.home"))
        return func(*args, **kwargs)

    return wrapper


def _filtered_events_query(query=None):
    query = query or Event.query
    if current_user.is_super_admin:
        return query
    return query.filter(Event.event_type == current_user.admin_scope)


def _ensure_event_access(event: Event):
    if current_user.is_super_admin:
        return
    if event.event_type != current_user.admin_scope:
        abort(403)


def _registration_query():
    query = Registration.query
    if current_user.is_super_admin:
        return query
    return query.join(Event).filter(Event.event_type == current_user.admin_scope)


def _event_type_options():
    if current_user.is_super_admin:
        return EVENT_CATEGORY_CHOICES
    return [current_user.admin_scope]


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    events = _filtered_events_query(Event.query).order_by(Event.start_time).all()
    total_registrations = _registration_query().count()
    upcoming_events = _filtered_events_query(
        Event.query.filter(Event.start_time >= datetime.utcnow())
    ).count()
    return render_template(
        "admin/dashboard.html",
        events=events,
        total_registrations=total_registrations,
        upcoming_events=upcoming_events,
        admin_scope=current_user.admin_scope,
    )


@admin_bp.route("/events/new", methods=["GET", "POST"])
@login_required
@admin_required
def create_event():
    event_type_choices = _event_type_options()
    if request.method == "POST":
        form = _event_form_data(request)
        if form["errors"]:
            for error in form["errors"]:
                flash(error, "danger")
            return render_template(
                "admin/event_form.html",
                event=None,
                form_defaults=_build_form_defaults(data=form["data"]),
                event_types=event_type_choices,
                form_action=url_for("admin.create_event"),
            )

        if not current_user.is_super_admin:
            form["data"]["event_type"] = current_user.admin_scope

        event = Event(**form["data"])
        db.session.add(event)
        db.session.commit()
        flash("Event created successfully.", "success")
        return redirect(url_for("admin.dashboard"))

    defaults = _build_form_defaults()
    if not current_user.is_super_admin:
        defaults["event_type"] = current_user.admin_scope

    return render_template(
        "admin/event_form.html",
        event=None,
        form_defaults=defaults,
        event_types=event_type_choices,
        form_action=url_for("admin.create_event"),
    )


@admin_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    _ensure_event_access(event)
    event_type_choices = _event_type_options()

    if request.method == "POST":
        form = _event_form_data(request)
        if form["errors"]:
            for error in form["errors"]:
                flash(error, "danger")
            return render_template(
                "admin/event_form.html",
                event=event,
                form_defaults=_build_form_defaults(data=form["data"]),
                event_types=event_type_choices,
                form_action=url_for("admin.edit_event", event_id=event.id),
            )

        if not current_user.is_super_admin:
            form["data"]["event_type"] = current_user.admin_scope

        for key, value in form["data"].items():
            setattr(event, key, value)
        db.session.commit()
        flash("Event updated successfully.", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template(
        "admin/event_form.html",
        event=event,
        form_defaults=_build_form_defaults(event=event),
        event_types=event_type_choices,
        form_action=url_for("admin.edit_event", event_id=event.id),
    )


@admin_bp.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    _ensure_event_access(event)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted successfully.", "info")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/events/<int:event_id>/registrations")
@login_required
@admin_required
def event_registrations(event_id: int):
    event = Event.query.get_or_404(event_id)
    _ensure_event_access(event)
    registrations = (
        Registration.query.filter_by(event_id=event.id)
        .order_by(Registration.created_at.desc())
        .all()
    )
    interests = (
        EventInterest.query.filter_by(event_id=event.id)
        .order_by(EventInterest.created_at.desc())
        .all()
    )
    return render_template("admin/registrations.html", event=event, registrations=registrations, interests=interests)


@admin_bp.route("/registrations/<int:registration_id>")
@login_required
@admin_required
def registration_detail(registration_id: int):
    registration = Registration.query.get_or_404(registration_id)
    attendee = registration.user
    _ensure_event_access(registration.event)
    other_registrations_query = Registration.query.filter(
        Registration.user_id == attendee.id, Registration.id != registration.id
    ).join(Event)
    if not current_user.is_super_admin:
        other_registrations_query = other_registrations_query.filter(
            Event.event_type == current_user.admin_scope
        )
    other_registrations = other_registrations_query.order_by(Event.start_time.desc()).all()
    return render_template(
        "admin/registration_detail.html",
        registration=registration,
        event=registration.event,
        attendee=attendee,
        other_registrations=other_registrations,
    )


def _event_form_data(req):
    """Extract and validate common event fields from request data."""
    data = {
        "title": req.form.get("title", "").strip(),
        "summary": req.form.get("summary", "").strip(),
        "description": req.form.get("description", "").strip(),
        "location": req.form.get("location", "").strip(),
        "image_url": req.form.get("image_url", "").strip() or None,
        "event_type": req.form.get("event_type", "").strip() or "General",
    }

    start_time_raw = req.form.get("start_time", "").strip()
    end_time_raw = req.form.get("end_time", "").strip()
    capacity_raw = req.form.get("capacity", "").strip()

    errors = []
    for field in ("title", "summary", "description", "location"):
        if not data[field]:
            errors.append(f"{field.replace('_', ' ').title()} is required.")

    try:
        data["start_time"] = datetime.fromisoformat(start_time_raw)
    except ValueError:
        errors.append("Start time must be a valid date/time.")
    try:
        data["end_time"] = datetime.fromisoformat(end_time_raw)
    except ValueError:
        errors.append("End time must be a valid date/time.")

    if "start_time" in data and "end_time" in data and data.get("start_time") and data.get("end_time"):
        if data["end_time"] <= data["start_time"]:
            errors.append("End time must be after the start time.")

    try:
        data["capacity"] = int(capacity_raw)
        if data["capacity"] <= 0:
            raise ValueError
    except ValueError:
        errors.append("Capacity must be a positive integer.")

    if data["event_type"] not in EVENT_CATEGORY_CHOICES:
        errors.append("Select a valid event type.")

    return {"data": data, "errors": errors}


def _build_form_defaults(event=None, data=None):
    """Prepare template-friendly defaults for the event form."""
    source = {}
    if data:
        source = data.copy()
    elif event:
        source = {
            "title": event.title,
            "summary": event.summary,
            "description": event.description,
            "location": event.location,
            "start_time": event.start_time,
            "end_time": event.end_time,
            "capacity": event.capacity,
            "image_url": event.image_url,
            "event_type": event.event_type,
        }

    start_time = source.get("start_time")
    end_time = source.get("end_time")

    def _format_datetime(value):
        if not value:
            return ""
        if isinstance(value, str):
            return value
        return value.strftime("%Y-%m-%dT%H:%M")

    defaults = {
        "title": source.get("title", ""),
        "summary": source.get("summary", ""),
        "description": source.get("description", ""),
        "location": source.get("location", ""),
        "start_time": _format_datetime(start_time),
        "end_time": _format_datetime(end_time),
        "capacity": source.get("capacity", 10),
        "image_url": source.get("image_url", "") or "",
        "event_type": source.get("event_type", EVENT_CATEGORY_CHOICES[0]),
    }

    return defaults
