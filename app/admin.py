from django.contrib import admin

from .models import Booking, Service


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone",
        "service",
        "preferred_date",
        "status",
        "created_at",
    )
    list_filter = ("status", "service", "preferred_date")
    list_editable = ("status",)
    search_fields = ("name", "phone", "service", "details")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("name", "phone", "service", "preferred_date", "details")}),
        ("Management", {"fields": ("status", "created_at")}),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name_hi", "name_en", "booking_service", "position", "is_active")
    list_editable = ("position", "is_active")
    list_filter = ("is_active",)
    search_fields = ("slug", "name_hi", "name_en", "description_hi", "description_en")
    prepopulated_fields = {"slug": ("name_en",)}
    ordering = ("position", "name_hi")
    fieldsets = (
        ("Service tile", {"fields": ("slug", "icon", "position", "is_active")}),
        ("Display names", {"fields": ("name_hi", "name_en")}),
        ("Descriptions shown when selected", {"fields": ("description_hi", "description_en")}),
        ("Booking form", {"fields": ("booking_service",)}),
    )
