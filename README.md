# Mess Calculator

Shared meal/expense tracker for small groups, built with Django.

## Local setup

1. **Create a Postgres database** (adjust names to taste):
   ```bash
   createuser mess_user -P
   createdb mess_manager -O mess_user
   ```

2. **Create a virtualenv and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # then edit .env: set SECRET_KEY, and DATABASE_URL to match the db you made above
   ```
   Generate a real SECRET_KEY:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Migrate and create an admin user:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Run it:**
   ```bash
   python manage.py runserver
   ```
   Visit http://127.0.0.1:8000/admin/ and log in.

## Project layout

- `accounts` — custom User model
- `groups` — Group, GroupMembership, invites (next up)
- `mess` — MonthCycle, MonthlyEnrollment, DailyEntry, calculations (next up)
- `auditlog` — append-only ActivityLog (next up)
- `notifications` — monthly email job (next up)

## Deployment

Configured for a PaaS (Render/Railway/Fly.io): `Procfile` defines the web
process (gunicorn) and a `release` step that runs migrations automatically
on each deploy. See the deployment guide for exact steps.
