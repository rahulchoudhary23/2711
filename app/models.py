from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


EVENT_CATEGORY_CHOICES = ["Arts", "Cultural", "Technical", "Science", "Sports"]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    admin_scope = db.Column(db.String(50), default="super")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship("Registration", back_populates="user", cascade="all, delete-orphan")
    interests = db.relationship("EventInterest", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_super_admin(self) -> bool:
        if not self.is_admin:
            return False
        if not self.admin_scope:
            return True
        return self.admin_scope.lower() == "super"


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    summary = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(80), nullable=False, default=EVENT_CATEGORY_CHOICES[0])
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship("Registration", back_populates="event", cascade="all, delete-orphan")
    interests = db.relationship("EventInterest", back_populates="event", cascade="all, delete-orphan")

    @property
    def seats_remaining(self) -> int:
        return max(self.capacity - len(self.registrations), 0)

    def has_space(self) -> bool:
        return self.seats_remaining > 0

    @property
    def date_label(self) -> str:
        return self.start_time.strftime("%B %d, %Y")

    @property
    def day_label(self) -> str:
        return self.start_time.strftime("%A")

    @property
    def time_range(self) -> str:
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)

    attendee_name = db.Column(db.String(150), nullable=False)
    attendee_email = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(120), nullable=True)
    section = db.Column(db.String(60), nullable=True)
    student_uid = db.Column(db.String(60), nullable=True)
    team_selection = db.Column(db.String(80), nullable=True)

    user = db.relationship("User", back_populates="registrations")
    event = db.relationship("Event", back_populates="registrations")

    __table_args__ = (db.UniqueConstraint("user_id", "event_id", name="unique_event_registration"),)


class EventInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.String(280), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)

    user = db.relationship("User", back_populates="interests")
    event = db.relationship("Event", back_populates="interests")

    __table_args__ = (db.UniqueConstraint("user_id", "event_id", name="unique_event_interest"),)


def seed_admin(name: str = "Event Admin", email: str = "admin@example.com", password: str = "admin123") -> Optional[User]:
    """Ensure there is at least one admin user for first-time setup."""
    admin_profiles = [
        {"name": name, "email": email, "password": password, "scope": "super"},
    ]
    for category in EVENT_CATEGORY_CHOICES:
        admin_profiles.append(
            {
                "name": f"{category} Admin",
                "email": f"{category.lower()}@eventmanage.io",
                "password": f"{category.lower()}123",
                "scope": category,
            }
        )

    created = False
    for profile in admin_profiles:
        existing = User.query.filter_by(email=profile["email"]).first()
        if existing:
            if not existing.is_admin:
                existing.is_admin = True
                created = True
            if existing.admin_scope != profile["scope"]:
                existing.admin_scope = profile["scope"]
                created = True
            continue
        new_admin = User(
            name=profile["name"],
            email=profile["email"],
            is_admin=True,
            admin_scope=profile["scope"],
        )
        new_admin.set_password(profile["password"])
        db.session.add(new_admin)
        created = True

    if created:
        db.session.commit()

    return User.query.filter_by(email=email).first()


def seed_sample_events() -> None:
    """Populate the database with sample events if they are missing."""
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    category_map = {
        "Workshop": "Technical",
        "Conference": "Technical",
        "Pitch Event": "Technical",
        "Bootcamp": "Technical",
        "Networking": "Cultural",
        "Hackathon": "Technical",
        "Talks": "Science",
        "Forum": "Science",
        "Masterclass": "Cultural",
        "Fireside Chat": "Cultural",
        "General": "Cultural",
        "Expo": "Cultural",
        "Clinic": "Technical",
        "Education": "Technical",
        "All": "Cultural",
    }

    pending_commit = False
    for event in Event.query.all():
        if event.event_type not in EVENT_CATEGORY_CHOICES:
            event.event_type = category_map.get(event.event_type, "Cultural")
            pending_commit = True

    quick_filter_samples = [
        Event(
            title="Campus Skills Combine",
            summary="Conditioning circuits, agility metrics, and panel feedback for student athletes happening today.",
            description="""<p>Rotate through speed, strength, and vision drills led by varsity coaches. Capture
            professional feedback and walk away with a training blueprint for the season.</p>""",
            location="North Field Pavilion",
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=6),
            capacity=50,
            event_type="Sports",
            image_url="https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="Gallery Sketch Jam",
            summary="Weekly arts meetup with live models, collaborative murals, and feedback corners.",
            description="""<p>Bring your favorite medium, explore guided warmups, and showcase work-in-progress pieces
            to the community. Materials table and acoustic playlist provided.</p>""",
            location="Studio 12 - Arts Annex",
            start_time=now + timedelta(days=3, hours=18),
            end_time=now + timedelta(days=3, hours=21),
            capacity=40,
            event_type="Arts",
            image_url="https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="Science Discovery Expo",
            summary="Monthly science fair covering lab breakthroughs, citizen science, and mentorship programs.",
            description="""<p>Visit expert booths, attend lightning lessons on emerging research methods, and match with
            mentors who align with your exploration goals.</p>""",
            location="Atrium Hall",
            start_time=now + timedelta(days=15, hours=12),
            end_time=now + timedelta(days=15, hours=18),
            capacity=200,
            event_type="Science",
            image_url="https://images.unsplash.com/photo-1523580846011-d3a5bc25702b?auto=format&fit=crop&w=900&q=80",
        ),
    ]
    samples = [
        Event(
            title="Design Thinking Workshop",
            summary="Reimagine customer journeys with collaborative design exercises.",
            description="""<p>Dive into the pillars of design thinking with rapid ideation rounds, empathy mapping,
            and low-fidelity prototyping challenges in small teams.</p>""",
            location="Innovation Hub, Downtown",
            start_time=now + timedelta(days=5, hours=10),
            end_time=now + timedelta(days=5, hours=13),
            capacity=40,
            event_type="Technical",
            image_url="https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="Tech Leaders Summit",
            summary="A strategic summit for engineering leaders exploring AI and cloud journeys.",
            description="""<p>Keynotes from industry experts, interactive breakouts, and curated peer roundtables.
            Includes a leadership clinic on scaling teams sustainably.</p>""",
            location="Grand Convention Center",
            start_time=now + timedelta(days=8, hours=9),
            end_time=now + timedelta(days=8, hours=17),
            capacity=220,
            event_type="Technical",
            image_url="https://images.unsplash.com/photo-1531058020387-3be344556be6?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="Startup Pitch Night",
            summary="Watch early-stage founders pitch to a live panel of investors.",
            description="""<p>Discover upcoming startups, provide feedback, and vote for the audience choice award.
            Networking mixer with investors after the pitches.</p>""",
            location="The Loft Space",
            start_time=now + timedelta(days=10, hours=18),
            end_time=now + timedelta(days=10, hours=21),
            capacity=120,
            event_type="Cultural",
            image_url="https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="Product Analytics Bootcamp",
            summary="Learn actionable analytics workflows for product discovery and growth.",
            description="""<p>Hands-on sessions covering funnel analysis, cohort tracking, experimentation design,
            and storytelling with data dashboards.</p>""",
            location="Campus Lab 3B",
            start_time=now + timedelta(days=12, hours=11),
            end_time=now + timedelta(days=12, hours=16),
            capacity=60,
            event_type="Technical",
            image_url="https://images.unsplash.com/photo-1525182008055-f88b95ff7980?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="Women in Tech Roundtable",
            summary="An inclusive conversation spotlighting career journeys and mentorship.",
            description="""<p>Hear from leaders shaping the tech landscape, join guided discussions, and match with
            mentors for ongoing support.</p>""",
            location="Skyline Lounge",
            start_time=now + timedelta(days=14, hours=17),
            end_time=now + timedelta(days=14, hours=19),
            capacity=80,
            event_type="Cultural",
            image_url="https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="Cloud Native Hackathon",
            summary="Build resilient services during a 24-hour cloud native challenge.",
            description="""<p>Teams design, deploy, and observe microservices with live mentorship and surprise
            infrastructure twists. Prizes for best reliability, velocity, and innovation.</p>""",
            location="Code Commons",
            start_time=now + timedelta(days=16, hours=9),
            end_time=now + timedelta(days=17, hours=9),
            capacity=150,
            event_type="Technical",
            image_url="https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="UX Research Lightning Talks",
            summary="Case studies on human-centered design and product discovery wins.",
            description="""<p>Short talks covering diary studies, rapid testing frameworks, and inclusive design.
            Followed by open Q&A and resource swaps.</p>""",
            location="Auditorium A",
            start_time=now + timedelta(days=18, hours=15),
            end_time=now + timedelta(days=18, hours=17),
            capacity=90,
            event_type="Science",
            image_url="https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="Innovation Culture Masterclass",
            summary="Frameworks to build experimentation-driven cultures in scaling orgs.",
            description="""<p>Interactive masterclass with playbooks, canvas exercises, and peer coaching to unlock
            experimentation inside your teams.</p>""",
            location="Strategy Studio",
            start_time=now + timedelta(days=20, hours=10),
            end_time=now + timedelta(days=20, hours=15),
            capacity=55,
            event_type="Cultural",
            image_url="https://images.unsplash.com/photo-1553877522-43269d4ea984?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="Sustainability in Tech Forum",
            summary="Discuss climate-forward engineering practices and green software.",
            description="""<p>Panels covering carbon-aware architectures, energy efficient code, and ESG reporting.
            Includes breakout roadmapping sessions.</p>""",
            location="Green Hall",
            start_time=now + timedelta(days=22, hours=9),
            end_time=now + timedelta(days=22, hours=16),
            capacity=180,
            event_type="Science",
            image_url="https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=900&q=80",
        ),
        Event(
            title="AI Ethics Fireside",
            summary="Explore responsible AI design with ethicists and product leaders.",
            description="""<p>An intimate fireside chat on accountability frameworks, governance, and inclusive
            datasets. Includes interactive scenario workshops.</p>""",
            location="Fireside Den",
            start_time=now + timedelta(days=24, hours=18),
            end_time=now + timedelta(days=24, hours=20),
            capacity=70,
            event_type="Cultural",
            image_url="https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=900&q=80",
        ),
    ]

    created = 0
    for event in quick_filter_samples + samples:
        if Event.query.filter_by(title=event.title).first():
            continue
        db.session.add(event)
        created += 1

    if created or pending_commit:
        db.session.commit()
