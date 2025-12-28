from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map_view'),
    path('api/stations/', views.station_geojson, name='station_geojson'),
    path('api/data/', views.fetch_data, name='fetch_data'),
]
