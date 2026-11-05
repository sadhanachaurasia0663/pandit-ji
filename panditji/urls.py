from django.contrib import admin
from django.urls import path

from app import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health", views.health, name="health"),
    path("api/bookings", views.create_booking, name="create_booking"),
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("", views.home, name="home"),
]
