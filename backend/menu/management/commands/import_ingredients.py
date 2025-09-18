import csv
import json
from pathlib import Path
from django.core.management.base import BaseCommand

from menu.models import Ingredient


class Command(BaseCommand):
    help = " ".join(
        [
            "Import ingredients from data/ingredients.json",
            "and data/ingredients.csv",
        ]
    )

    def add_arguments(self, parser):
        parser.add_argument("--dir", default="data")

    def handle(self, *args, **opts):
        base = Path(opts["dir"])
        items = set()
        jp = base / "ingredients.json"
        if jp.exists():
            data = json.loads(jp.read_text(encoding="utf-8"))
            for i in data:
                name = i.get("name") or i.get("title")
                unit = i.get("measurement_unit") or i.get("dimension") or ""
                if name and unit:
                    items.add((name.strip(), unit.strip()))
        cp = base / "ingredients.csv"
        if cp.exists():
            with cp.open("r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    name = row[0].strip()
                    unit = row[1].strip() if len(row) > 1 else ""
                    if name and unit:
                        items.add((name, unit))
        objs = []
        for name, unit in items:
            objs.append(Ingredient(name=name, measurement_unit=unit))
        Ingredient.objects.bulk_create(objs, ignore_conflicts=True)
        message = f"Imported {len(items)} ingredients"
        self.stdout.write(self.style.SUCCESS(message))
