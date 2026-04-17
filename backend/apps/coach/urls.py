from django.urls import path
from . import views

urlpatterns = [
    path("coach/analyze/", views.analyze_composition, name="coach-analyze"),
]
