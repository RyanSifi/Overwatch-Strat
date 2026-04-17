from django.urls import path
from . import views

urlpatterns = [
    path("profiles/me/",   views.profile_me,   name="profile-me"),
    path("profiles/sync/", views.profile_sync, name="profile-sync"),
]
