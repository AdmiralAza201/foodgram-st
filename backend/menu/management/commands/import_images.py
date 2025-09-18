from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = " ".join(
        [
            "Import all files from data/images to MEDIA/recipes",
            "(raw copy, no binding)",
        ]
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            default="data/images",
            help="Path to images directory",
        )

    def handle(self, *args, **opts):
        base = Path(opts["dir"])
        media = Path(settings.MEDIA_ROOT) / "recipes"
        media.mkdir(parents=True, exist_ok=True)
        count = 0
        for fp in base.glob("*.*"):
            if fp.is_file():
                (media / fp.name).write_bytes(fp.read_bytes())
                count += 1
        message = f"Copied {count} images to {media}"
        self.stdout.write(self.style.SUCCESS(message))
