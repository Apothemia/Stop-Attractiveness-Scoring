from django.urls import path
from .views import station_geojson, map_view

urlpatterns = [
    path('', map_view, name='map'),
    path('api/stations/', station_geojson, name='station_geojson'),
]
