import csv
from pathlib import Path

INPUT_CSV = '../data/UrbanBus/BUS_DATA_FEB_2018.csv'
OUTPUT_DIR = Path('daily_partitions')
DATE_COL = 'Ride_start_date'
CHECKPOINT = Path('checkpoint_rows.txt')
LOG_EVERY = 5_000_000

OUTPUT_DIR.mkdir(exist_ok=True)

start_row = int(CHECKPOINT.read_text()) if CHECKPOINT.exists() else 0
print(f'Resuming from row {start_row:,}')

open_files = {}
writers = {}

with open(INPUT_CSV, 'r', newline='', encoding='utf-8', buffering=1024 * 1024) as infile:
    reader = csv.reader(infile)

    header = next(reader)
    date_idx = header.index(DATE_COL)

    for _ in range(start_row):
        next(reader)

    def get_writer(day):
        if day in writers:
            return writers[day]

        out_path = OUTPUT_DIR / f'{day}.csv'
        exists = out_path.exists()

        f = open(out_path, 'a', newline='', encoding='utf-8')
        w = csv.writer(f)
        if not exists:
            w.writerow(header)

        open_files[day] = f
        writers[day] = w
        return w

    row_count = start_row

    for row in reader:
        get_writer(row[date_idx]).writerow(row)
        row_count += 1

        if row_count % LOG_EVERY == 0:
            CHECKPOINT.write_text(str(row_count))
            print(f'Processed {row_count:,} rows')

CHECKPOINT.write_text(str(row_count))

for f in open_files.values():
    f.close()
