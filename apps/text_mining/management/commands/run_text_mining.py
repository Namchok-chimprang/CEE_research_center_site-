from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.publications.models import Publication
from apps.text_mining.models import TextMiningRun
from apps.text_mining.services import (
    SOURCE_FIELD_CHOICES,
    run_text_mining,
    run_text_mining_for_all_publications,
)


class Command(BaseCommand):
    help = "Run text mining on all publications or a selected subset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--publication-id",
            action="append",
            dest="publication_ids",
            type=int,
            help="Publication IDs to analyze. Repeat the flag to pass multiple IDs.",
        )
        parser.add_argument(
            "--username",
            type=str,
            help="Optional username to associate with the run.",
        )
        parser.add_argument(
            "--title",
            type=str,
            help="Optional title for the run.",
        )
        parser.add_argument(
            "--source-field",
            action="append",
            dest="source_fields",
            choices=[value for value, _label in SOURCE_FIELD_CHOICES],
            help="Publication field to include in analysis. Repeat the flag to pass multiple fields.",
        )

    def handle(self, *args, **options):
        initiated_by = None
        username = options.get("username")
        if username:
            initiated_by = get_user_model().objects.filter(username=username).first()
            if initiated_by is None:
                raise CommandError(f"User '{username}' was not found.")

        publication_ids = options.get("publication_ids") or []
        source_fields = options.get("source_fields") or None
        if publication_ids:
            publications = Publication.objects.filter(pk__in=publication_ids)
            if not publications.exists():
                raise CommandError("No matching publications were found.")
            run = run_text_mining(
                publications,
                initiated_by=initiated_by,
                title=options.get("title") or "Management command text mining run",
                scope=TextMiningRun.SCOPE_SELECTED,
                source_fields=source_fields,
            )
        else:
            run = run_text_mining_for_all_publications(
                initiated_by=initiated_by,
                source_fields=source_fields,
                title=options.get("title"),
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed text mining run #{run.pk} for {run.analyzed_count} publication(s)."
            )
        )
