import pandas as pd
import os
from django.conf import settings

def calculate_station_scores():
    # Load Usage Data
    usage_path = os.path.join(settings.BASE_DIR, '../data/BART/date-hour-soo-dest-2025.csv')
    usage_cols = ['date', 'hour', 'source', 'destination', 'passengers']
    usage_df = pd.read_csv(usage_path, names=usage_cols, header=None)

    # Aggregating usage
    src_passenger_total = usage_df.groupby('source')['passengers'].sum()
    dest_passenger_total = usage_df.groupby('destination')['passengers'].sum()
    usage_score = (src_passenger_total + dest_passenger_total).fillna(0)
    print(usage_score)

    # Counting how many stop events happen at each stop_id
    stop_times_path = os.path.join(settings.BASE_DIR, '../data/BART/GTFS/stop_times.txt')
    stop_times = pd.read_csv(stop_times_path)
    frequency = stop_times['stop_id'].value_counts()

    # Normalisation and Weighting
    max_u = usage_score.max()
    max_f = frequency.max()

    w1, w2, w3 = 0.3, 0.5, 0.2

    # Create a lookup dictionary
    scores = {}
    for abbr in usage_score.index:
        u_norm = usage_score.get(abbr, 0) / max_u
        # Weighting: 70% Usage, 30% Frequency
        final_score = (u_norm * 0.7) + (0.3 * 0.5)
        scores[abbr] = round(final_score, 3)
        
    return scores
