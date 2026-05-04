from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("text_mining", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicationtextmining",
            name="primary_topic",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="publicationtextmining",
            name="topic_scores",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="textminingrun",
            name="source_fields",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="textminingrun",
            name="topic_summary",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
