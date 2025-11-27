from datetime import datetime, timedelta

from sqlalchemy import func, or_
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models import Event, EventInterest, Registration


events_bp = Blueprint("events", __name__)

TEAM_OPTIONS = [
    "Solo",
    "Pair",
    "Trio",
    "Squad",
    "Open Team",
]


@events_bp.route("/")
def home():
    now = datetime.utcnow()
    base_upcoming_query = Event.query.filter(Event.start_time >= now).order_by(Event.start_time)

    event_types = [row[0] for row in Event.query.with_entities(Event.event_type).distinct().order_by(Event.event_type).all()]
    search_query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "all")
    timeframe, selected_date, start_bound, end_bound = _resolve_timeframe(now)

    filtered_query = base_upcoming_query
    if selected_category != "all":
        filtered_query = filtered_query.filter(Event.event_type == selected_category)
    if search_query:
        pattern = f"%{search_query}%"
        filtered_query = filtered_query.filter(
            or_(
                Event.title.ilike(pattern),
                Event.summary.ilike(pattern),
                Event.location.ilike(pattern),
            )
        )
    if start_bound and end_bound:
        filtered_query = filtered_query.filter(Event.start_time >= start_bound, Event.start_time < end_bound)

    filtered_count = filtered_query.count()
    upcoming_events = filtered_query.limit(6).all()
    interested_event_ids = set()
    if current_user.is_authenticated:
        interested_event_ids = {
            row[0]
            for row in EventInterest.query.with_entities(EventInterest.event_id).filter_by(user_id=current_user.id)
        }

    total_events = Event.query.count()
    upcoming_count = base_upcoming_query.count()
    total_registrations = Registration.query.count()
    total_capacity = db.session.query(func.sum(Event.capacity)).scalar() or 0
    available_capacity = max(total_capacity - total_registrations, 0)
    capacity_percent = (total_registrations / total_capacity * 100) if total_capacity else 0

    next_event = upcoming_events[0] if upcoming_events else Event.query.order_by(Event.start_time).first()
    days_to_next_event = None
    if next_event:
        days_to_next_event = max((next_event.start_time.date() - now.date()).days, 0)

    projected_revenue = total_registrations * 85
    projected_checked_in = int(round(total_registrations * 0.6))
    projected_pending = max(total_registrations - projected_checked_in, 0)

    trend_points = []
    max_count = 0
    for offset in range(6, -1, -1):
        day_start = (now - timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = Registration.query.filter(Registration.created_at >= day_start, Registration.created_at < day_end).count()
        label = day_start.strftime("%b %d")
        trend_points.append({"label": label, "count": count})
        if count > max_count:
            max_count = count

    height_base = max(max_count, 1)
    for point in trend_points:
        point["height"] = round((point["count"] / height_base) * 100)

    recent_registrations = (
        Registration.query.order_by(Registration.created_at.desc()).limit(4).all()
    )

    location_candidates = Event.query.order_by(Event.start_time).limit(6).all()
    active_locations = []
    for candidate in location_candidates:
        if candidate.location not in active_locations:
            active_locations.append(candidate.location)
        if len(active_locations) == 3:
            break

    analytics = {
        "total_events": total_events,
        "upcoming_count": upcoming_count,
        "total_registrations": total_registrations,
        "total_capacity": total_capacity,
        "available_capacity": available_capacity,
        "capacity_percent": capacity_percent,
        "projected_revenue": projected_revenue,
        "projected_checked_in": projected_checked_in,
        "projected_pending": projected_pending,
        "days_to_next_event": days_to_next_event,
        "next_event": next_event,
        "trend": trend_points,
        "recent_registrations": recent_registrations,
        "active_locations": active_locations,
    }

    return render_template(
        "home.html",
        upcoming_events=upcoming_events,
        analytics=analytics,
        event_types=event_types,
        search_query=search_query,
        selected_category=selected_category,
        filtered_count=filtered_count,
        timeframe=timeframe,
        selected_date=selected_date,
        interested_event_ids=interested_event_ids,
    )


@events_bp.route("/events")
def events_list():
    now = datetime.utcnow()
    search_query = request.args.get("q", "").strip()
    selected_category = request.args.get("category", "all")
    timeframe, selected_date, start_bound, end_bound = _resolve_timeframe(now)

    events_query = Event.query.order_by(Event.start_time)
    if selected_category != "all":
        events_query = events_query.filter(Event.event_type == selected_category)
    if search_query:
        pattern = f"%{search_query}%"
        events_query = events_query.filter(
            or_(
                Event.title.ilike(pattern),
                Event.summary.ilike(pattern),
                Event.location.ilike(pattern),
            )
        )
    if start_bound and end_bound:
        events_query = events_query.filter(Event.start_time >= start_bound, Event.start_time < end_bound)

    events = events_query.all()
    interested_event_ids = set()
    if current_user.is_authenticated:
        interested_event_ids = {
            row[0]
            for row in EventInterest.query.with_entities(EventInterest.event_id).filter_by(user_id=current_user.id)
        }
    event_types = [row[0] for row in Event.query.with_entities(Event.event_type).distinct().order_by(Event.event_type).all()]

    return render_template(
        "events.html",
        events=events,
        event_types=event_types,
        search_query=search_query,
        selected_category=selected_category,
        total_results=len(events),
        timeframe=timeframe,
        selected_date=selected_date,
        interested_event_ids=interested_event_ids,
    )


@events_bp.route("/events/<int:event_id>")
def event_detail(event_id: int):
    event = Event.query.get_or_404(event_id)
    is_registered = False
    interest_record = None
    if current_user.is_authenticated:
        is_registered = (
            Registration.query.filter_by(user_id=current_user.id, event_id=event.id).first()
            is not None
        )
        interest_record = EventInterest.query.filter_by(user_id=current_user.id, event_id=event.id).first()

    return render_template(
        "event_detail.html",
        event=event,
        is_registered=is_registered,
        is_interested=interest_record is not None,
        interest_note=interest_record.note if interest_record and interest_record.note else "",
        team_options=TEAM_OPTIONS,
    )


@events_bp.route("/events/<int:event_id>/register", methods=["POST"])
@login_required
def register_for_event(event_id: int):
    event = Event.query.get_or_404(event_id)

    if not event.has_space():
        flash("This event is already full.", "warning")
        return redirect(url_for("events.event_detail", event_id=event.id))

    already_registered = Registration.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if already_registered:
        flash("You are already registered for this event.", "info")
        return redirect(url_for("events.event_detail", event_id=event.id))

    attendee_name = request.form.get("attendee_name", "").strip()
    attendee_email = request.form.get("attendee_email", "").strip()
    department = request.form.get("department", "").strip()
    section = request.form.get("section", "").strip()
    student_uid = request.form.get("student_uid", "").strip()
    team_selection = request.form.get("team_selection", "").strip()
    agreement = request.form.get("agreement")

    errors = []
    if not attendee_name:
        errors.append("Attendee name is required.")
    if not attendee_email:
        errors.append("Email address is required.")
    if not department:
        errors.append("Department is required.")
    if not section:
        errors.append("Section or batch is required.")
    if not student_uid:
        errors.append("Unique ID is required.")
    if not team_selection:
        errors.append("Please select a team preference.")
    if not agreement:
        errors.append("Please confirm that you agree to the participation rules.")
    if team_selection and team_selection not in TEAM_OPTIONS:
        errors.append("Select a valid team option.")

    if errors:
        for error in errors:
            flash(error, "danger")
        return redirect(url_for("events.event_detail", event_id=event.id))

    registration = Registration(
        user_id=current_user.id,
        event_id=event.id,
        attendee_name=attendee_name,
        attendee_email=attendee_email,
        department=department or None,
        section=section or None,
        student_uid=student_uid or None,
        team_selection=team_selection or None,
    )
    interest = EventInterest.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if interest:
        db.session.delete(interest)
    db.session.add(registration)
    db.session.commit()
    flash("You have been registered for the event!", "success")
    return redirect(url_for("events.event_detail", event_id=event.id))


@events_bp.route("/events/<int:event_id>/unregister", methods=["POST"])
@login_required
def unregister_from_event(event_id: int):
    event = Event.query.get_or_404(event_id)
    registration = Registration.query.filter_by(user_id=current_user.id, event_id=event.id).first()

    if not registration:
        flash("You are not registered for this event.", "warning")
        return redirect(url_for("events.event_detail", event_id=event.id))

    db.session.delete(registration)
    db.session.commit()
    flash("Your registration has been canceled.", "info")
    return redirect(url_for("events.event_detail", event_id=event.id))


@events_bp.route("/events/<int:event_id>/interest", methods=["POST"])
@login_required
def toggle_interest(event_id: int):
    event = Event.query.get_or_404(event_id)
    action = request.form.get("action", "save")
    note = request.form.get("note", "").strip()

    interest = EventInterest.query.filter_by(user_id=current_user.id, event_id=event.id).first()

    if action == "remove":
        if interest:
            db.session.delete(interest)
            db.session.commit()
            flash("Removed from the interest list.", "info")
        else:
            flash("You were not marked as interested.", "warning")
        return redirect(url_for("events.event_detail", event_id=event.id))

    if not interest:
        interest = EventInterest(user_id=current_user.id, event_id=event.id)
        db.session.add(interest)

    interest.note = note or None
    db.session.commit()
    flash("Thanks! We will keep you updated about this event.", "success")
    return redirect(url_for("events.event_detail", event_id=event.id))


@events_bp.route("/my-registrations")
@login_required
def my_registrations():
    registrations = (
        Registration.query.filter_by(user_id=current_user.id)
        .join(Event)
        .order_by(Event.start_time)
        .all()
    )
    return render_template("my_registrations.html", registrations=registrations)


@events_bp.app_context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


def _resolve_timeframe(now: datetime):
    timeframe = request.args.get("timeframe", "all").lower() or "all"
    selected_date = request.args.get("date", "")
    start_bound = end_bound = None

    def _start_of_day(dt: datetime):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    if timeframe == "today":
        start_bound = _start_of_day(now)
        end_bound = start_bound + timedelta(days=1)
    elif timeframe in {"this-week", "this_week"}:
        start_bound = _start_of_day(now - timedelta(days=now.weekday()))
        end_bound = start_bound + timedelta(days=7)
        timeframe = "this-week"
    elif timeframe in {"this-month", "this_month"}:
        start_bound = _start_of_day(now).replace(day=1)
        if start_bound.month == 12:
            end_bound = start_bound.replace(year=start_bound.year + 1, month=1)
        else:
            end_bound = start_bound.replace(month=start_bound.month + 1)
        timeframe = "this-month"
    elif timeframe == "date" and selected_date:
        try:
            parsed_date = datetime.strptime(selected_date, "%Y-%m-%d")
        except ValueError:
            timeframe = "all"
            selected_date = ""
        else:
            start_bound = _start_of_day(parsed_date)
            end_bound = start_bound + timedelta(days=1)
    else:
        timeframe = "all"
        selected_date = ""

    return timeframe, selected_date, start_bound, end_bound
