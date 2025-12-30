from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime
from .models import Stations, YearlyUsage
from .utils import station_attractiveness_scores_from_filtered_records


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


@require_http_methods(["GET"])
def station_scores(request):
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

    def _get_weight(param: str, default: float) -> float:
        v = request.GET.get(param, None)
        if v is None or v == '':
            return default
        try:
            return float(v)
        except ValueError:
            raise ValueError(f'Invalid {param}, must be a number')

    try:
        w1 = _get_weight('w1', 1.0 / 3.0)
        w2 = _get_weight('w2', 1.0 / 3.0)
        w3 = _get_weight('w3', 1.0 / 3.0)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    if w1 < 0 or w2 < 0 or w3 < 0:
        return JsonResponse({'error': 'Weights must be non-negative'}, status=400)

    s = w1 + w2 + w3
    if s <= 0:
        return JsonResponse({'error': 'At least one weight must be > 0'}, status=400)

    # Normalize server-side to guarantee sum=1
    w1, w2, w3 = (w1 / s, w2 / s, w3 / s)

    records = YearlyUsage.objects.filter(
        date__gte=start_date,
        date__lte=end_date,
    ).values('source', 'destination', 'passengers')

    scores_by_abbr = station_attractiveness_scores_from_filtered_records(
        records=records,
        weights=(w1, w2, w3),
    )

    payload = [
        {
            'abbr': abbr,
            **vals,
        }
        for abbr, vals in scores_by_abbr.items()
    ]
    payload.sort(key=lambda x: x.get('as', 0.0), reverse=True)

    return JsonResponse(
        {
            'start_date': str(start_date),
            'end_date': str(end_date),
            'weights': {'w1': w1, 'w2': w2, 'w3': w3},
            'count': len(payload),
            'results': payload,
        },
        safe=False
    )
