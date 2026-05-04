from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("publications", "0005_publicationtreelayout"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicationtreelayout",
            name="leaf_color",
            field=models.CharField(default="#6e8bdc", max_length=7),
        ),
    ]
