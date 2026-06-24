"""
URL configuration for socialhub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
