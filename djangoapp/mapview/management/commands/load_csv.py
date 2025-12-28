import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models, transaction


class Command(BaseCommand):
    help = 'Load station data from CSV into a specified model'
    BATCH_SIZE = 100_000

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--file',
            type=str,
            required=True,
            help='Path to the CSV file to load',
        )
        parser.add_argument(
            '-m', '--model',
            type=str,
            required=True,
            help='Name of the target model',
        )
        parser.add_argument(
            '-th', '--header',
            type=str,
            required=False,
            help='Header line for the CSV data',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['file'])
        model_name = options['model']

        if not csv_path.exists():
            self.stderr.write(f'> CSV not found: {csv_path}')
            return
        self.stdout.write(f'> CSV File Path: {csv_path}')

        try:
            Model: models.Model = apps.get_model('mapview', model_name)
        except LookupError:
            self.stderr.write(f"Model '{model_name}' not found in app 'mapview'.")
            return
        self.stdout.write(f'> Target Model: {Model}')

        objs = []
        total = 0

        with open(csv_path, newline='', encoding='utf-8') as f:
            headers = options.get('header', None)
            if headers is not None:
                reader = csv.DictReader(f, fieldnames=headers.split(','))
            else:
                reader = csv.DictReader(f)

            with transaction.atomic():
                for row in reader:
                    objs.append(Model(**row))

                    if len(objs) >= self.BATCH_SIZE:
                        Model.objects.bulk_create(objs, batch_size=self.BATCH_SIZE)
                        total += len(objs)
                        objs.clear()
                        self.stdout.write(f'>> Inserted {total:,} rows')

                if objs:
                    Model.objects.bulk_create(objs, batch_size=self.BATCH_SIZE)
                    total += len(objs)

        self.stdout.write(self.style.SUCCESS(f'> Inserted {total:,} rows into {model_name}'))
