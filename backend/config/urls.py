"""
URLs racines de l'application OW Coach.
Toutes les routes API sont préfixées /api/.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.heroes.urls")),
    path("api/", include("apps.tracker.urls")),
    path("api/", include("apps.coach.urls")),
    path("api/", include("apps.profiles.urls")),
    # Authentification via DRF token (login/logout/register gérés manuellement)
    path("api/auth/", include("rest_framework.urls")),
]
