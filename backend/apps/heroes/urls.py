"""
URLs pour les héros, maps et counter-picker.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Héros
    path("heroes/",                       views.HeroListView.as_view(),  name="hero-list"),
    path("heroes/<slug:slug>/",           views.HeroDetailView.as_view(), name="hero-detail"),
    path("heroes/<slug:slug>/counters/",  views.hero_counters,           name="hero-counters"),
    path("heroes/<slug:slug>/synergies/", views.hero_synergies,          name="hero-synergies"),

    # Méta
    path("meta/", views.MetaCompListView.as_view(), name="meta-list"),

    # Patch Notes
    path("patches/",            views.PatchNoteListView.as_view(),   name="patch-list"),
    path("patches/<str:version>/", views.PatchNoteDetailView.as_view(), name="patch-detail"),

    # Maps
    path("maps/",                    views.MapListView.as_view(),   name="map-list"),
    path("maps/<slug:slug>/guide/",  views.map_guide,               name="map-guide"),

    # Counter-picker
    path("counters/suggest/",        views.suggest_counters,        name="counters-suggest"),
]
