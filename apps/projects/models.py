from django.db import models
from django.urls import reverse


class ProjectCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    color = models.CharField(max_length=7, default="#4f46e5", help_text="Hex color, e.g. #4f46e5")
    map_x = models.PositiveIntegerField(default=50, help_text="Horizontal position in percent (0-100)")
    map_y = models.PositiveIntegerField(default=50, help_text="Vertical position in percent (0-100)")
    icon = models.CharField(max_length=8, blank=True, help_text="Optional emoji or short icon text")
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "Project categories"

    def __str__(self):
        return self.name


class ResearchProject(models.Model):
    class Status(models.TextChoices):
        ONGOING = "ongoing", "Ongoing"
        COMPLETED = "completed", "Completed"

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    fiscal_year = models.PositiveIntegerField()
    funding_source = models.CharField(max_length=255)
    principal_investigator = models.CharField(max_length=255)
    co_investigators = models.TextField(blank=True, help_text="One name per line or comma separated list.")
    budget_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    project_code = models.CharField(max_length=120, blank=True)
    cmu_mis_code = models.CharField(max_length=120, blank=True)
    imported_start_date_text = models.CharField(max_length=120, blank=True)
    imported_end_date_text = models.CharField(max_length=120, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONGOING)
    abstract = models.TextField(blank=True)
    outcomes = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fiscal_year", "display_order", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.slug])
