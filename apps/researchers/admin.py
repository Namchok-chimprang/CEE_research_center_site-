import io
import os

from django.contrib import admin, messages
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse

from .models import Researcher

ADMIN_SYNC_COUNT = 20


@admin.register(Researcher)
class ResearcherAdmin(admin.ModelAdmin):
    change_form_template = "admin/researchers/researcher/change_form.html"
    list_display = (
        'full_name',
        'organization_role',
        'team_name',
        'display_order',
        'scopus_author_id',
        'email',
        'is_active',
    )
    list_filter = ('organization_role', 'team_name', 'is_active')
    search_fields = (
        'full_name',
        'position',
        'expertise',
        'scopus_author_id',
        'team_name',
        'academic_status',
    )
    ordering = ('display_order', 'full_name')
    actions = ['sync_publications_from_scopus']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:researcher_id>/sync-scopus/",
                self.admin_site.admin_view(self.sync_researcher_view),
                name="researchers_researcher_sync_scopus",
            ),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["sync_scopus_url"] = reverse(
            "admin:researchers_researcher_sync_scopus",
            args=[object_id],
        )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    @admin.action(description="Sync selected researchers' publications from Scopus")
    def sync_publications_from_scopus(self, request, queryset):
        success_count = 0
        for researcher in queryset:
            ok, output = self.run_sync_for_researcher(researcher)
            if ok:
                success_count += 1
                self.message_user(
                    request,
                    f"Synced {researcher.full_name}. {summarize_output(output)}",
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    f"Failed for {researcher.full_name}. {output}",
                    level=messages.ERROR,
                )

        if success_count:
            self.message_user(
                request,
                f"Completed Scopus sync for {success_count} researcher(s).",
                level=messages.SUCCESS,
            )

    def sync_researcher_view(self, request, researcher_id):
        researcher = get_object_or_404(Researcher, pk=researcher_id)
        api_key = os.environ.get("SCOPUS_API_KEY", "")
        if api_key:
            self.message_user(
                request,
                f"Debug: SCOPUS_API_KEY is visible to this server process ({mask_secret(api_key)}).",
                level=messages.INFO,
            )
        else:
            self.message_user(
                request,
                "Debug: SCOPUS_API_KEY is NOT visible to this server process.",
                level=messages.WARNING,
            )
        ok, output = self.run_sync_for_researcher(researcher)
        if ok:
            self.message_user(
                request,
                f"Scopus sync finished for {researcher.full_name}. {summarize_output(output)}",
                level=messages.SUCCESS,
            )
        else:
            self.message_user(
                request,
                f"Scopus sync failed for {researcher.full_name}. {output}",
                level=messages.ERROR,
            )

        change_url = reverse("admin:researchers_researcher_change", args=[researcher.pk])
        return HttpResponseRedirect(change_url)

    def run_sync_for_researcher(self, researcher):
        stdout = io.StringIO()
        try:
            call_command(
                "sync_scopus",
                researcher_id=researcher.pk,
                count=ADMIN_SYNC_COUNT,
                stdout=stdout,
            )
        except Exception as exc:
            output = stdout.getvalue().strip()
            detail = output or str(exc)
            return False, detail
        return True, stdout.getvalue().strip()


def summarize_output(output):
    if not output:
        return "No additional output."
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return "No additional output."
    return lines[-1]


def mask_secret(value):
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"
