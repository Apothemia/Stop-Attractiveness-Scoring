from django.shortcuts import render
from django.http import JsonResponse
from .models import Stations
from .utils import calculate_station_scores


def station_geojson(request):
    scores = calculate_station_scores()

    data = [
        {
            'code': s.code,
            'name': s.name,
            'abbr': s.abbreviation,
            'lat': s.latitude,
            'lon': s.longitude,
            'score': scores.get(s.abbreviation, 0),
        }
        for s in Stations.objects.all()
    ]
    return JsonResponse(data, safe=False)


def map_view(request):
    return render(request, 'map.html')
