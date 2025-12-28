import pandas as pd
from pathlib import Path

from decorator import append

INPUT_DIR = Path('daily_partitions')
OUTPUT_DIR = Path('daily_partitions_parquet')

dtypes = {
    'Card_Number': 'int',
    'Card_Type': 'string',
    'Travel_Mode': 'string',
    'Bus_Service_Number': 'string',
    'Direction': 'string',
    'Bus_Trip_Num': 'string',
    'Bus_Reg_Num': 'string',
    'Boarding_stop_stn': 'string',
    'Alighting_stop_stn': 'string',
    'Ride_start_date': 'string',
    'Ride_start_time': 'string',
    'Ride_end_date': 'string',
    'Ride_end_time': 'string'
}

OUTPUT_DIR.mkdir(exist_ok=True)

for csv_path in sorted(INPUT_DIR.glob('*.csv')):
    parquet_path = OUTPUT_DIR / (csv_path.stem + '.parquet')

    if parquet_path.exists():
        print(f'Skipping {csv_path.name} (already converted)')
        continue

    print(f'Converting {csv_path.name} → Parquet')

    df = pd.read_csv(csv_path, dtype=dtypes)

    df['Ride_start_date'] = pd.to_datetime(
        df['Ride_start_date'],
        format='%Y-%m-%d'
    )
    df['Ride_start_time'] = pd.to_timedelta(
        df['Ride_start_time']
    )
    df['Ride_end_date'] = pd.to_datetime(
        df['Ride_end_date'],
        format='%Y-%m-%d'
    )
    df['Ride_end_time'] = pd.to_timedelta(
        df['Ride_end_time']
    )

    df.to_parquet(
        parquet_path,
        engine='pyarrow',
        compression='snappy',
        index=False
    )

    # chunks = pd.read_csv(
    #     csv_path,
    #     chunksize=CHUNK_SIZE
    # )
    #
    # first = True
    # for chunk in chunks:
    #     chunk.to_parquet(
    #         parquet_path,
    #         engine='pyarrow',
    #         compression=COMPRESSION,
    #         index=False,
    #         append=True
    #     )
    #     first = False
