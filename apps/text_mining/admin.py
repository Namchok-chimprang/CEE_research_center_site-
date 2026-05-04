from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse

from .forms import TextMiningRunForm
from .models import PublicationTextMining, TextMiningRun
from .services import run_text_mining_for_all_publications


def build_term_cloud(items):
    if not items:
        return []
    max_score = max(item.get("score", 0) for item in items) or 1
    min_size = 1.05
    max_size = 2.55
    cloud = []
    palette = ["#60a5fa", "#34d399", "#f59e0b", "#f472b6", "#a78bfa", "#f87171"]
    for index, item in enumerate(items):
        scale = item.get("score", 0) / max_score
        font_size = min_size + (max_size - min_size) * scale
        cloud.append(
            {
                **item,
                "font_size": round(font_size, 2),
                "rotate": -6 if index % 3 == 0 else (4 if index % 4 == 0 else 0),
                "color": palette[index % len(palette)],
            }
        )
    return cloud


def build_bar_rows(items, key):
    if not items:
        return []
    max_count = max(item[key] for item in items) or 1
    rows = []
    for item in items:
        rows.append(
            {
                **item,
                "width_pct": max(10, round((item[key] / max_count) * 100)),
            }
        )
    return rows


@admin.register(TextMiningRun)
class TextMiningRunAdmin(admin.ModelAdmin):
    change_list_template = "admin/text_mining/textminingrun/change_list.html"
    list_display = (
        "title",
        "scope",
        "status",
        "publication_count",
        "analyzed_count",
        "display_source_fields",
        "initiated_by",
        "created_at",
    )
    list_filter = ("scope", "status", "created_at")
    search_fields = ("title", "notes", "error_message")
    readonly_fields = (
        "scope",
        "status",
        "publication_count",
        "analyzed_count",
        "source_fields",
        "top_terms",
        "topic_summary",
        "notes",
        "error_message",
        "started_at",
        "finished_at",
        "created_at",
        "updated_at",
        "initiated_by",
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "run-all/",
                self.admin_site.admin_view(self.run_all_view),
                name="text_mining_textminingrun_run_all",
            ),
            path(
                "start/",
                self.admin_site.admin_view(self.start_run_view),
                name="text_mining_textminingrun_start",
            ),
            path(
                "dashboard/",
                self.admin_site.admin_view(self.dashboard_view),
                name="text_mining_textminingrun_dashboard",
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["run_all_url"] = reverse("admin:text_mining_textminingrun_run_all")
        extra_context["start_run_url"] = reverse("admin:text_mining_textminingrun_start")
        extra_context["dashboard_url"] = reverse("admin:text_mining_textminingrun_dashboard")
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description="Source fields")
    def display_source_fields(self, obj):
        return ", ".join(obj.source_fields or [])

    def run_all_view(self, request):
        run = run_text_mining_for_all_publications(
            initiated_by=request.user if request.user.is_authenticated else None
        )
        self.message_user(
            request,
            f"Text mining completed for {run.analyzed_count} publication(s).",
            level=messages.SUCCESS,
        )
        return HttpResponseRedirect(reverse("admin:text_mining_textminingrun_changelist"))

    def start_run_view(self, request):
        if request.method == "POST":
            form = TextMiningRunForm(request.POST)
            if form.is_valid():
                run = run_text_mining_for_all_publications(
                    initiated_by=request.user if request.user.is_authenticated else None,
                    title=form.cleaned_data["title"] or None,
                    source_fields=form.cleaned_data["source_fields"],
                )
                self.message_user(
                    request,
                    f"Text mining completed for {run.analyzed_count} publication(s).",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(reverse("admin:text_mining_textminingrun_dashboard"))
        else:
            form = TextMiningRunForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "form": form,
            "title": "Start text mining run",
        }
        return render(request, "admin/text_mining/textminingrun/start_run.html", context)

    def dashboard_view(self, request):
        latest_run = TextMiningRun.objects.filter(status=TextMiningRun.STATUS_COMPLETED).first()
        results = latest_run.results.select_related("publication")[:12] if latest_run else []
        top_terms = build_bar_rows(latest_run.top_terms, "score") if latest_run else []
        topic_summary = build_bar_rows(latest_run.topic_summary, "count") if latest_run else []
        term_cloud = build_term_cloud(latest_run.top_terms) if latest_run else []
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Text mining dashboard",
            "latest_run": latest_run,
            "results": results,
            "top_terms": top_terms,
            "topic_summary": topic_summary,
            "term_cloud": term_cloud,
        }
        return render(request, "admin/text_mining/textminingrun/dashboard.html", context)


@admin.register(PublicationTextMining)
class PublicationTextMiningAdmin(admin.ModelAdmin):
    list_display = (
        "publication",
        "run",
        "primary_topic",
        "token_count",
        "unique_token_count",
        "generated_keywords",
        "created_at",
    )
    list_filter = ("run", "primary_topic", "created_at")
    search_fields = (
        "publication__title",
        "generated_keywords",
        "summary",
    )
    readonly_fields = (
        "publication",
        "run",
        "source_text",
        "token_count",
        "unique_token_count",
        "primary_topic",
        "topic_scores",
        "dominant_terms",
        "dominant_bigrams",
        "generated_keywords",
        "summary",
        "created_at",
    )

    def get_model_perms(self, request):
        return {}
