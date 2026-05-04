from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Publication, PublicationTreeLayout


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'corresponding_author',
        'journal',
        'sdg_goals',
        'published_date',
        'source',
        'journal_quartile',
        'impact_factor',
        'is_featured',
    )
    list_filter = ('source', 'is_featured', 'published_date', 'journal_quartile')
    search_fields = (
        'title',
        'authors',
        'all_authors',
        'corresponding_author',
        'keywords',
        'sdg_goals',
        'journal',
        'doi',
        'scopus_eid',
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PublicationTreeLayout)
class PublicationTreeLayoutAdmin(admin.ModelAdmin):
    change_form_template = "admin/publications/publicationtreelayout/change_form.html"
    list_display = (
        "title",
        "preset_key",
        "leaf_count",
        "is_active",
        "tree_editor_link",
        "preview_link",
    )
    list_filter = ("is_active", "preset_key", "leaf_count")
    search_fields = ("title", "branch_image")
    fieldsets = (
        (
            "Preset",
            {
                "fields": (
                    "title",
                    "preset_key",
                    "is_active",
                    "leaf_count",
                )
            },
        ),
        (
            "Tree Image",
            {
                "fields": (
                    "branch_image",
                    "branch_size",
                    "branch_position",
                )
            },
        ),
        (
            "Leaf Radius",
            {
                "fields": (
                    "base_radius",
                    "radius_gain",
                    "default_leaf_scale",
                    "leaf_color",
                    "default_leaf_opacity",
                )
            },
        ),
        (
            "Leaf Anchors",
            {
                "description": "Each X/Y pair is the center point of a leaf, using a 0-1 scale across the preview area.",
                "fields": (
                    ("leaf_1_x", "leaf_1_y", "leaf_1_scale", "leaf_1_color", "leaf_1_opacity"),
                    ("leaf_2_x", "leaf_2_y", "leaf_2_scale", "leaf_2_color", "leaf_2_opacity"),
                    ("leaf_3_x", "leaf_3_y", "leaf_3_scale", "leaf_3_color", "leaf_3_opacity"),
                    ("leaf_4_x", "leaf_4_y", "leaf_4_scale", "leaf_4_color", "leaf_4_opacity"),
                    ("leaf_5_x", "leaf_5_y", "leaf_5_scale", "leaf_5_color", "leaf_5_opacity"),
                ),
            },
        ),
    )

    @admin.display(description="Preview")
    def preview_link(self, obj):
        url = reverse("admin:publications_publicationtreelayout_change", args=[obj.pk])
        return format_html('<a href="{}">Open preview</a>', url)

    @admin.display(description="Tree Editor")
    def tree_editor_link(self, obj):
        url = reverse("publications:tree_editor", args=[obj.pk])
        return format_html('<a href="{}">Open tree editor</a>', url)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        tree_layout = PublicationTreeLayout.objects.get(pk=object_id)
        extra_context["tree_editor_url"] = reverse("publications:tree_editor", args=[tree_layout.pk])
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
