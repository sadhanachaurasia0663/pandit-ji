import json
import re
import smtplib
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core import mail
from django.test import Client, TestCase, override_settings

from .models import Booking, Service


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_HOST="smtp.example.com",
    EMAIL_HOST_USER="bookings@example.com",
    EMAIL_HOST_PASSWORD="test-password",
    EMAIL_PORT=587,
    DEFAULT_FROM_EMAIL="bookings@example.com",
    BOOKING_ADMIN_EMAIL="admin@example.com",
)
class BookingSiteTests(TestCase):
    def test_public_site_and_admin_access(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "बुकिंग विवरण")
        self.assertContains(response, 'name="viewport"')
        self.assertContains(response, "styles.css?v=11")
        self.assertContains(response, 'rel="canonical"')
        self.assertContains(response, 'property="og:type" content="website"')
        self.assertContains(response, 'id="business-structured-data"')
        self.assertContains(response, 'href="http://testserver/"')
        self.assertContains(response, 'data-language="hi"')
        self.assertContains(response, 'data-language="en"')
        self.assertEqual(response.content.count(b'data-language="hi"'), 1)
        self.assertEqual(response.content.count(b'data-language="en"'), 1)
        self.assertContains(response, "app.js?v=10")
        self.assertNotContains(response, 'href="#')
        self.assertContains(response, 'data-open-booking')
        self.assertContains(response, 'class="nav-contact-language"')
        self.assertLess(
            response.content.index(b'data-i18n="navContact"'),
            response.content.index(b'data-language="hi"'),
        )
        translations = (Path(settings.BASE_DIR) / "static" / "app.js").read_text()
        language_blocks = re.findall(
            r"(?s)^\s{2}(hi|en): \{(.*?)^\s{2}\},?$",
            translations,
            re.MULTILINE,
        )
        self.assertEqual({language for language, _ in language_blocks}, {"hi", "en"})
        template_keys = set(
            re.findall(
                r'data-i18n(?:-aria|-placeholder)?="([^"]+)"',
                response.content.decode(),
            )
        )
        translated_keys = {
            language: set(
                re.findall(r"^\s{4}([A-Za-z]\w*):", block, re.MULTILINE)
            )
            for language, block in language_blocks
        }
        for language in ("hi", "en"):
            self.assertTrue(template_keys.issubset(translated_keys[language]))
        self.assertEqual(translated_keys["hi"], translated_keys["en"])
        self.assertNotContains(response, "लॉग इन करें")
        self.assertEqual(self.client.get("/admin/app/booking/").status_code, 302)

    def test_booking_navigation_restores_the_booking_form(self):
        script = (Path(settings.BASE_DIR) / "static" / "app.js").read_text()
        self.assertIn(
            "document.querySelectorAll('[data-open-booking]')",
            script,
        )
        self.assertRegex(
            script,
            r"data-open-booking[\s\S]*?showBookingForm\(\);",
        )
        self.assertIn("serviceDetail.hidden = true;", script)
        self.assertIn("form.hidden = false;", script)

    def test_seo_crawl_endpoints(self):
        robots_response = self.client.get("/robots.txt")
        self.assertEqual(robots_response.status_code, 200)
        self.assertEqual(robots_response["Content-Type"], "text/plain; charset=utf-8")
        self.assertContains(robots_response, "Disallow: /admin/")
        self.assertContains(robots_response, "Sitemap: http://testserver/sitemap.xml")

        sitemap_response = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap_response.status_code, 200)
        self.assertEqual(sitemap_response["Content-Type"], "application/xml; charset=utf-8")
        sitemap = ElementTree.fromstring(sitemap_response.content)
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        self.assertEqual(
            sitemap.findtext("s:url/s:loc", namespaces=namespace),
            "http://testserver/",
        )

        home_response = self.client.get("/")
        structured_data = re.search(
            r'<script id="business-structured-data" type="application/json">(.*?)</script>',
            home_response.content.decode(),
        )
        self.assertIsNotNone(structured_data)
        self.assertEqual(json.loads(structured_data.group(1))["@type"], "LocalBusiness")

    def test_service_tiles_render_admin_managed_bilingual_content(self):
        response = self.client.get("/")
        services = list(Service.objects.order_by("position"))

        self.assertEqual(len(services), 4)
        self.assertContains(response, 'data-service-slug="astrology"')
        self.assertContains(response, 'class="service-icon"')
        for service in services:
            self.assertContains(response, f">{service.icon}</span>")
        self.assertContains(response, "description_hi")
        self.assertContains(response, "description_en")
        self.assertTrue(all(service.description_hi and service.description_en for service in services))

    def test_service_description_changes_in_admin_are_shown_on_the_page(self):
        service = Service.objects.get(slug="astrology")
        service.description_en = "Updated from the administration interface."
        service.save(update_fields=["description_en"])

        response = self.client.get("/")
        self.assertContains(response, "Updated from the administration interface.")

    def test_styles_include_mobile_layout_breakpoints(self):
        styles = (Path(settings.BASE_DIR) / "static" / "styles.css").read_text()
        self.assertIn("@media (max-width: 760px)", styles)
        self.assertIn("@media (max-width: 420px)", styles)

    def test_booking_submission_requires_csrf_and_sends_email(self):
        client = Client(enforce_csrf_checks=True)
        home_response = client.get("/")
        token = re.search(
            rb'name="csrfmiddlewaretoken" value="([^"]+)"',
            home_response.content,
        ).group(1).decode()

        response = client.post(
            "/api/bookings",
            data=json.dumps(
                {
                    "name": "Test Customer",
                    "phone": "1234567890",
                    "service": "Puja",
                    "preferred_date": "2027-05-11",
                    "details": "Test location",
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
        self.assertEqual(response.json()["status"], "new")
        self.assertEqual(Booking.objects.count(), 1)

    def test_booking_is_saved_when_email_delivery_fails(self):
        with patch(
            "app.views.EmailMessage.send",
            side_effect=smtplib.SMTPException("Mail server unavailable"),
        ):
            response = self.client.post(
                "/api/bookings",
                data=json.dumps(
                    {
                        "name": "Test Customer",
                        "phone": "1234567890",
                        "service": "Puja",
                        "preferred_date": "2027-05-11",
                        "details": "Test location",
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["booking_id"], 1)
        self.assertEqual(Booking.objects.count(), 1)

    @override_settings(BOOKING_ADMIN_EMAIL="")
    def test_booking_is_saved_and_configuration_error_is_reported(self):
        response = self.client.post(
            "/api/bookings",
            data=json.dumps(
                {
                    "name": "Test Customer",
                    "phone": "1234567890",
                    "service": "Puja",
                    "preferred_date": "2027-05-11",
                    "details": "Test location",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["booking_id"], 1)
        self.assertIn("ADMIN_EMAIL", response.json()["detail"])
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_booking_submission_validates_input(self):
        response = self.client.post(
            "/api/bookings",
            data=json.dumps({"name": "A"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("at least 2 characters", response.json()["detail"])
        self.assertEqual(len(mail.outbox), 0)

    def test_bookings_cannot_be_listed_from_the_public_api(self):
        response = self.client.get("/api/bookings")
        self.assertEqual(response.status_code, 405)

    def test_staff_can_view_bookings_in_the_admin(self):
        Booking.objects.create(
            name="Admin Test",
            phone="1234567890",
            service="Puja",
            preferred_date="2027-05-11",
            details="Test location",
        )
        user_model = get_user_model()
        user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )

        self.assertTrue(self.client.login(username="admin", password="test-password"))
        response = self.client.get("/admin/app/booking/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Test")

    def test_staff_can_manage_service_descriptions_in_admin(self):
        user_model = get_user_model()
        user_model.objects.create_superuser(
            username="service-admin",
            email="service-admin@example.com",
            password="test-password",
        )
        self.assertTrue(
            self.client.login(username="service-admin", password="test-password")
        )

        response = self.client.get("/admin/app/service/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ज्योतिष परामर्श")
        self.assertContains(response, "Astrology consultation")
