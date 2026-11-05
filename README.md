# Pandit Ji booking app

Django booking site, installable PWA, and private Django admin interface. Visitors can submit booking requests without creating an account or logging in. Staff manage bookings at `/admin/`; the admin requires a Django staff account.

## Run locally

```bash
source ../panditji_venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --fake-initial
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000 for the public booking site and http://127.0.0.1:8000/admin/ for booking management. On a new database, `--fake-initial` safely behaves like a regular migration. It also adopts the existing `data/pandit_ji.db` bookings table without recreating it.

If you see `table "bookings" already exists`, rerun `python manage.py migrate --fake-initial`. This records the existing initial booking migration and applies the remaining migrations without deleting bookings. Do not drop the table or delete the database.

Booking requests are saved in `data/pandit_ji.db` and an email notification is sent to `ADMIN_EMAIL` in the project-root `.env` file. Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and `ADMIN_EMAIL`. If `ADMIN_EMAIL` is blank, notifications go to `SMTP_USERNAME`. For Gmail, use an app password for `SMTP_PASSWORD`. If email configuration is missing or delivery fails, the booking is still saved and the response includes its reference number. `.env` is excluded from Git; keep it private.

## MySQL (optional)

To use MySQL instead of the default SQLite database, set `DATABASE_URL` in `.env` to a URL such as `mysql://pandit_user:password@localhost:3306/pandit_ji`. URL-encode special characters in the username or password, then run the migrations as shown above.

## Admin access

Create the first admin account with `python manage.py createsuperuser`. This account is only for the private Django admin; no public user login or registration is provided.

In the admin, open **Services** to edit the Hindi and English names and descriptions shown when visitors select a service tile. Use the active and position fields to control which tiles appear and their order. Visitors can return to the booking form from a service description, and the matching booking type is preselected.

## Mobile app

The public site is a PWA. Open it in Chrome on Android and choose **Install app**. It runs as a standalone app and keeps the main page available offline.

## Search engines

The public page includes a canonical URL, Hindi metadata, social-sharing metadata, and LocalBusiness structured data. `/robots.txt` points crawlers to `/sitemap.xml`; the sitemap currently lists the public home page. Navigation between page sections does not add a fragment (`#`) to the URL.
