from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("publications", "0007_publicationtreelayout_leaf_style_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_1_sdg",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_2_sdg",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_3_sdg",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_4_sdg",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_5_sdg",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
