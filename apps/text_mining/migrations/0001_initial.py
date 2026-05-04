from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("publications", "0004_publication_sdg_goals"),
    ]

    operations = [
        migrations.CreateModel(
            name="TextMiningRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("scope", models.CharField(choices=[("all", "All publications"), ("selected", "Selected publications")], default="selected", max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("publication_count", models.PositiveIntegerField(default=0)),
                ("analyzed_count", models.PositiveIntegerField(default=0)),
                ("top_terms", models.JSONField(blank=True, default=list)),
                ("notes", models.TextField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("initiated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="text_mining_runs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PublicationTextMining",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_text", models.TextField(blank=True)),
                ("token_count", models.PositiveIntegerField(default=0)),
                ("unique_token_count", models.PositiveIntegerField(default=0)),
                ("dominant_terms", models.JSONField(blank=True, default=list)),
                ("dominant_bigrams", models.JSONField(blank=True, default=list)),
                ("generated_keywords", models.CharField(blank=True, max_length=500)),
                ("summary", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("publication", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="text_mining_results", to="publications.publication")),
                ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="results", to="text_mining.textminingrun")),
            ],
            options={
                "ordering": ["publication__title"],
                "unique_together": {("publication", "run")},
            },
        ),
    ]
