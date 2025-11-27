# Event Management Platform

A full-stack Flask application for browsing, registering, and administering events. The project includes responsive HTML/CSS/JavaScript templates, user authentication, admin tooling, and an SQLite database backend.

## Features

- Public pages for home, event listings, and detailed event views
- User registration, login, and personal registration history
- Admin dashboard with event creation, editing, deletion, and registration insights
- Responsive UI built with modern CSS and lightweight JavaScript enhancements
- SQLite persistence powered by SQLAlchemy models
- Rich event metadata (type, schedule, availability) and colorful cards for every listing
- Custom registration form capturing attendee credentials (department, section, UID, team preference)
- Personal account area with profile overview and password management

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Create and activate a virtual environment (recommended).

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies.

   ```powershell
   pip install -r requirements.txt
   ```



4. Run the development server.

   ```powershell
   flask --app app run
   ```

The application automatically seeds a default administrator account on first launch:

- Email: `admin@example.com`
- Password: `admin123`

Change these credentials immediately in a production setting.

On first run, the database seeds a curated catalog of ten upcoming events across workshops, conferences, hackathons, and more to showcase the UI.

## Project Structure

```
app/
  __init__.py
  admin.py
  auth.py
  events.py
  models.py
  static/
    css/styles.css
    js/main.js
  templates/
    base.html
    ...
app.py
config.py
requirements.txt
```

## Environment Variables

You can override configuration defaults using environment variables:

- `SECRET_KEY` – Flask session secret
- `DATABASE_URL` – SQLAlchemy connection string

Store sensitive overrides in a `.env` file or environment-specific configuration.

## Running Tests

Currently no automated tests are bundled. Add pytest suites under a `tests/` directory as the project grows.

## Deployment Notes

- Configure a persistent database before deploying to production.
- Set `FLASK_ENV=production` and `FLASK_DEBUG=0` when deploying.
- Serve static files via a production-ready web server or CDN when possible.
