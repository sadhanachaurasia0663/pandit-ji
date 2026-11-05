from django.db import models
from django.utils import timezone


BOOKING_SERVICE_CHOICES = [
    ("astrology", "Astrology consultation"),
    ("kundli", "Birth chart preparation"),
    ("wedding", "Marriage matching / ceremony"),
    ("bhagwat", "Bhagwat Katha / Sunderkand"),
    ("housewarming", "Housewarming puja"),
    ("navgraha", "Navgraha Shanti"),
    ("thread-ceremony", "Sacred thread ceremony"),
]


class Service(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    icon = models.CharField(max_length=12, default="ॐ")
    name_hi = models.CharField("Hindi name", max_length=100)
    name_en = models.CharField("English name", max_length=100)
    description_hi = models.TextField("Hindi description")
    description_en = models.TextField("English description")
    booking_service = models.CharField(
        max_length=100,
        choices=BOOKING_SERVICE_CHOICES,
        help_text="Booking form option to select when a visitor books this service.",
    )
    position = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["position", "name_hi"]
        verbose_name = "service"
        verbose_name_plural = "services"

    def __str__(self):
        return self.name_hi


class Booking(models.Model):
    STATUS_NEW = "new"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    service = models.CharField(max_length=100)
    preferred_date = models.DateField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "bookings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.service}"
