from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from .models import Stations, YearlyUsage


def map_view(request):
    return render(request, 'map.html')


def station_geojson(request):
    data = [
        {
            'code': s.code,
            'name': s.name,
            'abbr': s.abbreviation,
            'lat': s.latitude,
            'lon': s.longitude
        }
        for s in Stations.objects.all()
    ]
    return JsonResponse(data, safe=False)


@require_http_methods(["GET"])
def fetch_data(request):
    model = request.GET.get('model', 'YearlyUsage')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not start_date_str or not end_date_str:
        return JsonResponse({'error': 'Missing start_date or end_date'}, status=400)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

    date_diff = (end_date - start_date).days
    if date_diff > 7:
        return JsonResponse({'error': 'Date range cannot exceed 7 days'}, status=400)

    if start_date > end_date:
        return JsonResponse({'error': 'Start date must be before or equal to end date'}, status=400)

    try:
        if model == 'YearlyUsage':
            records = YearlyUsage.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).values('date', 'hour', 'source', 'destination', 'passengers').order_by('date', 'hour')

            data = [
                {
                    'date': str(record['date']),
                    'hour': record['hour'],
                    'source': record['source'],
                    'destination': record['destination'],
                    'passengers': record['passengers'],
                }
                for record in records
            ]
        else:
            return JsonResponse({'error': f'Model {model} not supported'}, status=400)

        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
