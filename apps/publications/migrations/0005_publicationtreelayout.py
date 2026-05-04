from django.db import migrations, models


def create_default_tree_layouts(apps, schema_editor):
    PublicationTreeLayout = apps.get_model("publications", "PublicationTreeLayout")
    defaults = [
        {
            "preset_key": "five",
            "title": "Tree with 5 leaves",
            "branch_image": "images/tree-background-five.svg",
            "branch_size": "80% auto",
            "branch_position": "center 77%",
            "leaf_count": 5,
            "base_radius": 52,
            "radius_gain": 18,
            "default_leaf_scale": "1.00",
            "leaf_1_x": "0.190",
            "leaf_1_y": "0.190",
            "leaf_2_x": "0.380",
            "leaf_2_y": "0.100",
            "leaf_3_x": "0.580",
            "leaf_3_y": "0.190",
            "leaf_4_x": "0.140",
            "leaf_4_y": "0.380",
            "leaf_5_x": "0.650",
            "leaf_5_y": "0.370",
        },
        {
            "preset_key": "four",
            "title": "Tree with 4 leaves",
            "branch_image": "images/tree-background-three.svg",
            "branch_size": "74% auto",
            "branch_position": "center 84%",
            "leaf_count": 4,
            "base_radius": 50,
            "radius_gain": 16,
            "default_leaf_scale": "1.00",
            "leaf_1_x": "0.350",
            "leaf_1_y": "0.500",
            "leaf_2_x": "0.540",
            "leaf_2_y": "0.400",
            "leaf_3_x": "0.660",
            "leaf_3_y": "0.580",
            "leaf_4_x": "0.220",
            "leaf_4_y": "0.580",
            "leaf_5_x": "0.220",
            "leaf_5_y": "0.580",
        },
        {
            "preset_key": "three",
            "title": "Tree with 3 leaves",
            "branch_image": "images/tree-background-four.svg",
            "branch_size": "70% auto",
            "branch_position": "center 80%",
            "leaf_count": 3,
            "base_radius": 54,
            "radius_gain": 18,
            "default_leaf_scale": "1.00",
            "leaf_1_x": "0.400",
            "leaf_1_y": "0.300",
            "leaf_2_x": "0.570",
            "leaf_2_y": "0.120",
            "leaf_3_x": "0.750",
            "leaf_3_y": "0.400",
            "leaf_4_x": "0.750",
            "leaf_4_y": "0.400",
            "leaf_5_x": "0.750",
            "leaf_5_y": "0.400",
        },
    ]
    for data in defaults:
        PublicationTreeLayout.objects.update_or_create(
            preset_key=data["preset_key"],
            defaults=data,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("publications", "0004_publication_sdg_goals"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicationTreeLayout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("preset_key", models.CharField(choices=[("five", "5 leaves"), ("four", "4 leaves"), ("three", "3 leaves")], max_length=20, unique=True)),
                ("title", models.CharField(max_length=120)),
                ("is_active", models.BooleanField(default=True)),
                ("branch_image", models.CharField(help_text="Path relative to static/, e.g. images/tree-background-five.svg", max_length=255)),
                ("branch_size", models.CharField(default="80% auto", max_length=40)),
                ("branch_position", models.CharField(default="center 76%", max_length=40)),
                ("leaf_count", models.PositiveSmallIntegerField(default=5)),
                ("base_radius", models.PositiveSmallIntegerField(default=52)),
                ("radius_gain", models.PositiveSmallIntegerField(default=18)),
                ("default_leaf_scale", models.DecimalField(decimal_places=2, default=1.0, max_digits=4)),
                ("leaf_1_x", models.DecimalField(decimal_places=3, default=0.17, max_digits=5)),
                ("leaf_1_y", models.DecimalField(decimal_places=3, default=0.22, max_digits=5)),
                ("leaf_2_x", models.DecimalField(decimal_places=3, default=0.37, max_digits=5)),
                ("leaf_2_y", models.DecimalField(decimal_places=3, default=0.11, max_digits=5)),
                ("leaf_3_x", models.DecimalField(decimal_places=3, default=0.6, max_digits=5)),
                ("leaf_3_y", models.DecimalField(decimal_places=3, default=0.22, max_digits=5)),
                ("leaf_4_x", models.DecimalField(decimal_places=3, default=0.12, max_digits=5)),
                ("leaf_4_y", models.DecimalField(decimal_places=3, default=0.42, max_digits=5)),
                ("leaf_5_x", models.DecimalField(decimal_places=3, default=0.65, max_digits=5)),
                ("leaf_5_y", models.DecimalField(decimal_places=3, default=0.41, max_digits=5)),
            ],
            options={
                "ordering": ["preset_key"],
                "verbose_name": "Publication Tree Layout",
                "verbose_name_plural": "Publication Tree Layouts",
            },
        ),
        migrations.RunPython(create_default_tree_layouts, migrations.RunPython.noop),
    ]
