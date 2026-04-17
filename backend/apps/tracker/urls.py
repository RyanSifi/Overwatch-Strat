"""
URLs pour le tracker de parties.
"""
from django.urls import path
from . import views

urlpatterns = [
    path("tracker/sessions/",        views.GameSessionListCreateView.as_view(), name="session-list-create"),
    path("tracker/sessions/<int:pk>/", views.GameSessionDeleteView.as_view(),   name="session-delete"),
    path("tracker/stats/",           views.tracker_stats,                       name="tracker-stats"),
]
