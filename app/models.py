from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="student")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))


# ------------------------------
# Seeder Functions
# ------------------------------
def seed_admin():
    admin = User.query.filter_by(email="admin@demo.com").first()
    if not admin:
        admin = User(email="admin@demo.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()


def seed_sample_events():
    if Event.query.count() == 0:
        e1 = Event(title="Welcome Event", description="First event")
        e2 = Event(title="Tech Talk", description="AI & ML introduction")
        db.session.add_all([e1, e2])
        db.session.commit()

