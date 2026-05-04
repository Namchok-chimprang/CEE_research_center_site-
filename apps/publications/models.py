from django.conf import settings
from django.db import models


class Publication(models.Model):
    title = models.CharField(max_length=255)
    abstract = models.TextField(blank=True)
    authors = models.CharField(max_length=255)
    all_authors = models.TextField(blank=True)
    corresponding_author = models.CharField(max_length=255, blank=True)
    published_date = models.DateField(blank=True, null=True)
    journal = models.CharField(max_length=255, blank=True)
    keywords = models.CharField(max_length=255, blank=True)
    sdg_goals = models.CharField(
        max_length=120,
        blank=True,
        help_text='Comma-separated SDG numbers, e.g. 3,4,9,13',
    )
    file = models.FileField(upload_to='publications/', blank=True, null=True)
    external_url = models.URLField(blank=True)
    source = models.CharField(max_length=50, default='manual')
    scopus_eid = models.CharField(max_length=100, blank=True, null=True, unique=True)
    scopus_id = models.CharField(max_length=50, blank=True)
    scopus_source_id = models.CharField(max_length=50, blank=True)
    doi = models.CharField(max_length=255, blank=True)
    issn = models.CharField(max_length=20, blank=True)
    eissn = models.CharField(max_length=20, blank=True)
    journal_quartile = models.CharField(max_length=10, blank=True)
    journal_quartile_basis = models.CharField(max_length=100, blank=True)
    citescore = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    citescore_percentile = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    sjr = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    snip = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    impact_factor = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    impact_factor_source = models.CharField(max_length=100, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date', '-created_at']

    def __str__(self):
        return self.title

    def sdg_goal_numbers(self):
        if not self.sdg_goals:
            return []
        values = []
        for token in self.sdg_goals.split(','):
            token = token.strip()
            if token.isdigit():
                number = int(token)
                if 1 <= number <= 17 and number not in values:
                    values.append(number)
        return values


class PublicationTreeLayout(models.Model):
    PRESET_FIVE = "five"
    PRESET_FOUR = "four"
    PRESET_THREE = "three"

    PRESET_CHOICES = [
        (PRESET_FIVE, "5 leaves"),
        (PRESET_FOUR, "4 leaves"),
        (PRESET_THREE, "3 leaves"),
    ]

    preset_key = models.CharField(max_length=20, choices=PRESET_CHOICES, unique=True)
    title = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    branch_image = models.CharField(
        max_length=255,
        help_text="Path relative to static/, e.g. images/tree-background-five.svg",
    )
    branch_size = models.CharField(max_length=40, default="80% auto")
    branch_position = models.CharField(max_length=40, default="center 76%")
    leaf_count = models.PositiveSmallIntegerField(default=5)
    base_radius = models.PositiveSmallIntegerField(default=52)
    radius_gain = models.PositiveSmallIntegerField(default=18)
    default_leaf_scale = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    leaf_color = models.CharField(max_length=7, default="#6e8bdc")
    default_leaf_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.42)
    leaf_1_sdg = models.PositiveSmallIntegerField(blank=True, null=True)
    leaf_1_x = models.DecimalField(max_digits=5, decimal_places=3, default=0.170)
    leaf_1_y = models.DecimalField(max_digits=5, decimal_places=3, default=0.220)
    leaf_1_scale = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    leaf_1_color = models.CharField(max_length=7, blank=True, default="")
    leaf_1_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.42)
    leaf_2_sdg = models.PositiveSmallIntegerField(blank=True, null=True)
    leaf_2_x = models.DecimalField(max_digits=5, decimal_places=3, default=0.370)
    leaf_2_y = models.DecimalField(max_digits=5, decimal_places=3, default=0.110)
    leaf_2_scale = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    leaf_2_color = models.CharField(max_length=7, blank=True, default="")
    leaf_2_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.42)
    leaf_3_sdg = models.PositiveSmallIntegerField(blank=True, null=True)
    leaf_3_x = models.DecimalField(max_digits=5, decimal_places=3, default=0.600)
    leaf_3_y = models.DecimalField(max_digits=5, decimal_places=3, default=0.220)
    leaf_3_scale = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    leaf_3_color = models.CharField(max_length=7, blank=True, default="")
    leaf_3_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.42)
    leaf_4_sdg = models.PositiveSmallIntegerField(blank=True, null=True)
    leaf_4_x = models.DecimalField(max_digits=5, decimal_places=3, default=0.120)
    leaf_4_y = models.DecimalField(max_digits=5, decimal_places=3, default=0.420)
    leaf_4_scale = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    leaf_4_color = models.CharField(max_length=7, blank=True, default="")
    leaf_4_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.42)
    leaf_5_sdg = models.PositiveSmallIntegerField(blank=True, null=True)
    leaf_5_x = models.DecimalField(max_digits=5, decimal_places=3, default=0.650)
    leaf_5_y = models.DecimalField(max_digits=5, decimal_places=3, default=0.410)
    leaf_5_scale = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    leaf_5_color = models.CharField(max_length=7, blank=True, default="")
    leaf_5_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.42)

    class Meta:
        ordering = ["preset_key"]
        verbose_name = "Publication Tree Layout"
        verbose_name_plural = "Publication Tree Layouts"

    def __str__(self):
        return self.title

    def branch_image_url(self):
        relative = self.branch_image.lstrip("/")
        static_url = settings.STATIC_URL
        if not static_url.endswith("/"):
            static_url += "/"
        if not static_url.startswith("/"):
            static_url = "/" + static_url
        return f"{static_url}{relative}"

    def anchors(self):
        points = []
        for index in range(1, self.leaf_count + 1):
            points.append(
                {
                    "x": float(getattr(self, f"leaf_{index}_x")),
                    "y": float(getattr(self, f"leaf_{index}_y")),
                    "scale": float(getattr(self, f"leaf_{index}_scale")),
                    "color": getattr(self, f"leaf_{index}_color") or self.leaf_color,
                    "opacity": float(getattr(self, f"leaf_{index}_opacity")),
                }
            )
        return points

    def selected_sdg_numbers(self):
        return [getattr(self, f"leaf_{index}_sdg") for index in range(1, self.leaf_count + 1)]

    def as_frontend_config(self):
        return {
            "leafCount": self.leaf_count,
            "title": self.title,
            "branchImage": self.branch_image_url(),
            "branchSize": self.branch_size,
            "branchPosition": self.branch_position,
            "baseRadius": self.base_radius,
            "radiusGain": self.radius_gain,
            "defaultLeafScale": float(self.default_leaf_scale),
            "leafColor": self.leaf_color,
            "defaultLeafOpacity": float(self.default_leaf_opacity),
            "sdgNumbers": self.selected_sdg_numbers(),
            "anchors": self.anchors(),
        }
