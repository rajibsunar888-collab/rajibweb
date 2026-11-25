# Rajib Sunar - Portfolio (Django backend)

Your existing design, now connected to a Django backend.

## What the backend does
- **Contact form** saves every message in the database, emails you a notification (reply goes straight to the visitor), and blocks spam with a honeypot field, per-IP rate limiting and optional Cloudflare Turnstile CAPTCHA. CSRF protection is on.
- **Admin panel** (`/admin/`) to edit your profile and phone/email/social links, skills, projects, services, gallery images, and to read contact messages. No HTML editing needed.
- **Projects** on the home page and the Projects page come from the database.
- **CV download** is counted and can be replaced by uploading a new PDF in the admin.

## More features
- **Quote request page** (`/quote/`): service, budget, deadline and details. Saved in the admin under *Quote requests* (with a status you can change) and emailed to you. Each service card links to it with the service preselected.
- **Blog** (`/blog/`): write posts in the admin under *Blog posts* (plain text, blank line = new paragraph, optional cover image and YouTube link). The latest 3 show on the home page.
- **YouTube feed**: in the admin open *Site profile* and fill **YouTube channel ID** (starts with `UC`, found in YouTube Studio > Settings > Channel > Advanced settings). The latest 3 videos then show on the home page. No API key is needed. If it is empty or YouTube is unreachable, the section is simply hidden.
- **Testimonials**: visitors can submit a review; it stays hidden until you tick **Approved** in the admin (you also get an email).
- **Newsletter**: emails are collected under *Subscribers*, and you can export them as CSV with the admin action.
- **Analytics**: log in to the admin and click **View site analytics** (or open `/analytics/`) for page views, top pages, CV downloads, unread messages, new quotes and subscribers. Staff, bots and admin pages are not counted, and no IP addresses are stored for page views.

All forms use the same protection: CSRF, server-side validation, a honeypot field, per-IP rate limiting and (optional) Turnstile.

## Run it on your computer
```bash
python -m venv venv
venv\Scripts\activate            # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data       # loads your current projects, skills, services
python manage.py createsuperuser # your admin login
python manage.py runserver
```
Open http://127.0.0.1:8000/ and http://127.0.0.1:8000/admin/

**Images:** copy your `img` folder files into `static/img/` (see the note in that folder).

## Email notifications
Without settings, emails are printed in the terminal (development). To receive real emails, set
`EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` (a Gmail *App Password*, not your normal password) - see `.env.example`.
Messages are always saved in the admin even if email fails.

## Real CAPTCHA (optional, free)
Create a Cloudflare Turnstile widget, then set `TURNSTILE_SITE_KEY` and `TURNSTILE_SECRET_KEY`.
The verification box then appears on the form and is checked on the server.

## Deploy (Render / Railway / PythonAnywhere)
1. Set the environment variables from `.env.example` (`DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, your domain in `DJANGO_ALLOWED_HOSTS`).
2. Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
3. Start: `gunicorn config.wsgi`
4. Uploaded files (gallery, CV) need persistent storage or a cloud bucket on most hosts.
5. For PostgreSQL set `DB_ENGINE=postgres` and the `DB_*` variables (also `pip install psycopg[binary]`).

## Tests
`python manage.py test`
