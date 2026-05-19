import io
import os
import tempfile

from django.contrib import admin, messages
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse

from .models import ProjectCategory, ResearchProject


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "display_order", "is_active", "map_x", "map_y", "color")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("display_order", "name")
    list_editable = ("display_order", "is_active", "map_x", "map_y", "color")


@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    change_list_template = "admin/projects/researchproject/change_list.html"
    list_display = (
        "title",
        "category",
        "fiscal_year",
        "project_code",
        "cmu_mis_code",
        "funding_source",
        "principal_investigator",
        "status",
        "is_featured",
        "is_published",
    )
    list_filter = ("category", "status", "fiscal_year", "funding_source", "is_featured", "is_published")
    search_fields = (
        "title",
        "category__name",
        "project_code",
        "cmu_mis_code",
        "principal_investigator",
        "co_investigators",
        "funding_source",
        "abstract",
    )
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-fiscal_year", "display_order", "title")
    list_editable = ("category", "status", "is_featured", "is_published")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="projects_researchproject_import_csv",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["import_csv_url"] = reverse("admin:projects_researchproject_import_csv")
        return super().changelist_view(request, extra_context=extra_context)

    def import_csv_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Import Research Projects from CSV",
            "changelist_url": reverse("admin:projects_researchproject_changelist"),
        }

        if request.method == "POST":
            uploaded_file = request.FILES.get("csv_file")
            dry_run = request.POST.get("dry_run") == "on"

            if not uploaded_file:
                self.message_user(request, "Please choose a CSV file to import.", level=messages.ERROR)
                return render(request, "admin/projects/researchproject/import_csv.html", context)

            if not uploaded_file.name.lower().endswith(".csv"):
                self.message_user(request, "Only .csv files are supported.", level=messages.ERROR)
                return render(request, "admin/projects/researchproject/import_csv.html", context)

            stdout = io.StringIO()
            tmp_path = ""
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    for chunk in uploaded_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                call_command(
                    "import_projects",
                    file=tmp_path,
                    dry_run=dry_run,
                    stdout=stdout,
                )
                summary = stdout.getvalue().strip().splitlines()[-1] if stdout.getvalue().strip() else "Import completed."
                self.message_user(request, summary, level=messages.SUCCESS)
                return HttpResponseRedirect(reverse("admin:projects_researchproject_changelist"))
            except Exception as exc:
                details = stdout.getvalue().strip()
                message = f"Import failed: {exc}"
                if details:
                    message = f"{message} | Details: {details.splitlines()[-1]}"
                self.message_user(request, message, level=messages.ERROR)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

        return render(request, "admin/projects/researchproject/import_csv.html", context)
