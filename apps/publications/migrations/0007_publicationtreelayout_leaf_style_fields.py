from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("publications", "0006_publicationtreelayout_leaf_color"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicationtreelayout",
            name="default_leaf_opacity",
            field=models.DecimalField(decimal_places=2, default=0.42, max_digits=3),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_1_color",
            field=models.CharField(blank=True, default="", max_length=7),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_1_opacity",
            field=models.DecimalField(decimal_places=2, default=0.42, max_digits=3),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_1_scale",
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=4),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_2_color",
            field=models.CharField(blank=True, default="", max_length=7),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_2_opacity",
            field=models.DecimalField(decimal_places=2, default=0.42, max_digits=3),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_2_scale",
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=4),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_3_color",
            field=models.CharField(blank=True, default="", max_length=7),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_3_opacity",
            field=models.DecimalField(decimal_places=2, default=0.42, max_digits=3),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_3_scale",
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=4),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_4_color",
            field=models.CharField(blank=True, default="", max_length=7),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_4_opacity",
            field=models.DecimalField(decimal_places=2, default=0.42, max_digits=3),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_4_scale",
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=4),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_5_color",
            field=models.CharField(blank=True, default="", max_length=7),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_5_opacity",
            field=models.DecimalField(decimal_places=2, default=0.42, max_digits=3),
        ),
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_5_scale",
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=4),
        ),
    ]
