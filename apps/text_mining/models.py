from django.conf import settings
from django.db import models

from apps.publications.models import Publication


class TextMiningRun(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    SCOPE_ALL = "all"
    SCOPE_SELECTED = "selected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]
    SCOPE_CHOICES = [
        (SCOPE_ALL, "All publications"),
        (SCOPE_SELECTED, "Selected publications"),
    ]

    title = models.CharField(max_length=255)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=SCOPE_SELECTED)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    publication_count = models.PositiveIntegerField(default=0)
    analyzed_count = models.PositiveIntegerField(default=0)
    source_fields = models.JSONField(default=list, blank=True)
    top_terms = models.JSONField(default=list, blank=True)
    topic_summary = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="text_mining_runs",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class PublicationTextMining(models.Model):
    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name="text_mining_results",
    )
    run = models.ForeignKey(
        TextMiningRun,
        on_delete=models.CASCADE,
        related_name="results",
    )
    source_text = models.TextField(blank=True)
    token_count = models.PositiveIntegerField(default=0)
    unique_token_count = models.PositiveIntegerField(default=0)
    primary_topic = models.CharField(max_length=100, blank=True)
    topic_scores = models.JSONField(default=list, blank=True)
    dominant_terms = models.JSONField(default=list, blank=True)
    dominant_bigrams = models.JSONField(default=list, blank=True)
    generated_keywords = models.CharField(max_length=500, blank=True)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["publication__title"]
        unique_together = ("publication", "run")

    def __str__(self):
        return f"{self.publication} | {self.run}"
