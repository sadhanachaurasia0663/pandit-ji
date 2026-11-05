import json
import logging
import smtplib
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .forms import BookingRequestForm
from .models import Booking, Service

logger = logging.getLogger(__name__)


@require_GET
def home(request):
    services = list(
        Service.objects.filter(is_active=True).values(
            "slug",
            "icon",
            "name_hi",
            "name_en",
            "description_hi",
            "description_en",
            "booking_service",
        )
    )
    canonical_url = request.build_absolute_uri("/")
    return render(
        request,
        "home.html",
        {
            "services": services,
            "canonical_url": canonical_url,
            "structured_data": {
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "name": "Pandit Ji Near Dehradun",
                "description": (
                    "Astrology consultations, puja and Vedic ceremony bookings "
                    "in Dehradun and nearby areas."
                ),
                "url": canonical_url,
                "telephone": ["+91-8077847343", "+91-9927977462"],
                "areaServed": {
                    "@type": "City",
                    "name": "Dehradun",
                },
            },
        },
    )


@require_GET
def robots(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    return HttpResponse(
        f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /api/\nSitemap: {sitemap_url}\n",
        content_type="text/plain; charset=utf-8",
    )


@require_GET
def sitemap(request):
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    urlset = Element("urlset", xmlns=namespace)
    url = SubElement(urlset, "url")
    SubElement(url, "loc").text = request.build_absolute_uri("/")
    return HttpResponse(
        tostring(urlset, encoding="utf-8", xml_declaration=True),
        content_type="application/xml; charset=utf-8",
    )


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_GET
def service_worker(request):
    worker_path = Path(settings.BASE_DIR) / "static" / "sw.js"
    response = HttpResponse(worker_path.read_bytes(), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


@require_POST
def create_booking(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Booking details must be valid JSON."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Booking details must be a JSON object."}, status=400)

    form = BookingRequestForm(payload)
    if not form.is_valid():
        first_error = next(iter(form.errors.get_json_data().values()))[0]["message"]
        return JsonResponse({"detail": first_error}, status=400)

    missing = [
        name
        for name, value in (
            ("SMTP_HOST", settings.EMAIL_HOST),
            ("SMTP_USERNAME", settings.EMAIL_HOST_USER),
            ("SMTP_PASSWORD", settings.EMAIL_HOST_PASSWORD),
            ("SMTP_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL),
            ("ADMIN_EMAIL", settings.BOOKING_ADMIN_EMAIL),
        )
        if not value
    ]
    if missing:
        logger.error("Booking email is not configured; missing %s", ", ".join(missing))
    elif not 1 <= settings.EMAIL_PORT <= 65535:
        logger.error("SMTP_PORT must be between 1 and 65535")
        missing = ["SMTP_PORT"]
    else:
        try:
            validate_email(settings.BOOKING_ADMIN_EMAIL)
        except ValidationError:
            logger.error("ADMIN_EMAIL must be a valid email address")
            missing = ["ADMIN_EMAIL (valid email address required)"]

    booking_data = form.cleaned_data
    booking = Booking.objects.create(**booking_data)

    if missing:
        return JsonResponse(
            {
                "detail": (
                    "Booking was saved, but email is not configured. Set these server "
                    f"environment variables: {', '.join(missing)}."
                ),
                "booking_id": booking.pk,
            },
            status=503,
        )

    email = EmailMessage(
        subject="New puja booking request",
        body="\n".join(
            (
                "A new booking request was submitted.",
                "",
                f"Booking reference: {booking.pk}",
                f"Name: {booking_data['name']}",
                f"Mobile number: {booking_data['phone']}",
                f"Service: {booking_data['service']}",
                f"Preferred date: {booking_data['preferred_date'].isoformat()}",
                f"Location or additional details: {booking_data['details']}",
            )
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.BOOKING_ADMIN_EMAIL],
    )

    try:
        if email.send(fail_silently=False) != 1:
            raise smtplib.SMTPException("Booking notification was not accepted by the mail backend")
    except (OSError, smtplib.SMTPException, ImproperlyConfigured, ValueError):
        logger.exception("Failed to send booking notification email")
        return JsonResponse(
            {
                "detail": "Booking was saved, but the notification email could not be sent.",
                "booking_id": booking.pk,
            },
            status=502,
        )

    return JsonResponse(
        {
            "id": booking.pk,
            "name": booking.name,
            "phone": booking.phone,
            "service": booking.service,
            "preferred_date": booking.preferred_date.isoformat(),
            "details": booking.details,
            "status": booking.status,
            "created_at": booking.created_at.isoformat(),
        },
        status=201,
    )
