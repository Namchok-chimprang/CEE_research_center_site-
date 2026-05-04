from django.db import models


class Researcher(models.Model):
    class OrganizationRole(models.TextChoices):
        DIRECTOR = 'director', 'Director'
        DEPUTY_DIRECTOR = 'deputy_director', 'Deputy Director'
        SECRETARY = 'secretary', 'Secretary'
        TEAM_LEAD = 'team_lead', 'Team Lead'
        RESEARCHER = 'researcher', 'Researcher'
        PART_TIME_RESEARCHER = 'part_time_researcher', 'Part-time Researcher'

    full_name = models.CharField(max_length=255)
    title = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=255)
    organization_role = models.CharField(
        max_length=30,
        choices=OrganizationRole.choices,
        default=OrganizationRole.RESEARCHER,
    )
    team_name = models.CharField(max_length=255, blank=True)
    academic_status = models.CharField(max_length=255, blank=True)
    expertise = models.CharField(max_length=255, blank=True)
    scopus_author_id = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    profile_image = models.ImageField(upload_to='researchers/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'full_name']

    def __str__(self):
        return self.full_name

    @property
    def profile_label(self):
        return f"{self.title} {self.full_name}".strip()
