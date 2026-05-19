from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list, name="list"),
    path("city/", views.city_map, name="city"),
    path("city-alt/", views.city_map_alt, name="city_alt"),
    path("city/data/", views.city_map_data, name="city_data"),
    path("<slug:slug>/", views.project_detail, name="detail"),
]
