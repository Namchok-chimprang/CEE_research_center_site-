from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .forms import PublicationTreeLayoutForm
from .models import Publication, PublicationTreeLayout


SDG_LOOKUP = {
    1: {"label": "No Poverty", "color": "#E5243B"},
    2: {"label": "Zero Hunger", "color": "#DDA63A"},
    3: {"label": "Good Health", "color": "#4C9F38"},
    4: {"label": "Quality Education", "color": "#C5192D"},
    5: {"label": "Gender Equality", "color": "#FF3A21"},
    6: {"label": "Clean Water", "color": "#26BDE2"},
    7: {"label": "Clean Energy", "color": "#FCC30B"},
    8: {"label": "Decent Work", "color": "#A21942"},
    9: {"label": "Industry and Innovation", "color": "#FD6925"},
    10: {"label": "Reduced Inequalities", "color": "#DD1367"},
    11: {"label": "Sustainable Cities", "color": "#FD9D24"},
    12: {"label": "Responsible Consumption", "color": "#BF8B2E"},
    13: {"label": "Climate Action", "color": "#3F7E44"},
    14: {"label": "Life Below Water", "color": "#0A97D9"},
    15: {"label": "Life on Land", "color": "#56C02B"},
    16: {"label": "Peace and Justice", "color": "#00689D"},
    17: {"label": "Partnerships", "color": "#19486A"},
}


def demo_count_for_sdg(number):
    return ((number * 7) % 17) + 4


def select_spread_sdg_preview(sdg_summary, count=8):
    items = sorted(
        sdg_summary,
        key=lambda item: (-item["visual_count"], item["number"]),
    )
    if len(items) <= count:
        return items

    picked = []
    max_index = len(items) - 1
    for slot in range(count):
        index = round(slot * max_index / max(1, count - 1))
        candidate = items[index]
        if candidate["number"] not in {item["number"] for item in picked}:
            picked.append(candidate)

    if len(picked) < count:
        for candidate in items:
            if candidate["number"] not in {item["number"] for item in picked}:
                picked.append(candidate)
            if len(picked) == count:
                break

    return picked


def build_publication_sdg_context(publications):
    sdg_counts = {number: 0 for number in SDG_LOOKUP}
    publication_cards = []

    for publication in publications:
        goals = publication.sdg_goal_numbers()
        for goal in goals:
            sdg_counts[goal] += 1
        publication_cards.append(
            {
                "obj": publication,
                "sdg_numbers": goals,
            }
        )

    sdg_summary = [
        {
            "number": number,
            "label": SDG_LOOKUP[number]["label"],
            "color": SDG_LOOKUP[number]["color"],
            "count": sdg_counts[number],
            "visual_count": sdg_counts[number] if sdg_counts[number] > 0 else demo_count_for_sdg(number),
        }
        for number in SDG_LOOKUP
    ]
    sdg_featured = sorted(
        sdg_summary,
        key=lambda item: (-item["visual_count"], item["number"]),
    )[:8]

    return {
        "publication_cards": publication_cards,
        "sdg_summary": sdg_summary,
        "sdg_featured": sdg_featured,
        "left_featured": sdg_featured[:4],
        "right_featured": sdg_featured[4:8],
        "active_sdg_count": sum(1 for item in sdg_summary if item["count"] > 0),
        "max_sdg_count": max((item["visual_count"] for item in sdg_summary), default=0),
    }


@xframe_options_sameorigin
def publication_list(request):
    publications = Publication.objects.all()
    admin_preview = request.GET.get("admin_preview") == "1"
    initial_preset = request.GET.get("preset") or PublicationTreeLayout.PRESET_FIVE
    tree_layouts = {
        layout.preset_key: layout.as_frontend_config()
        for layout in PublicationTreeLayout.objects.filter(is_active=True)
    }
    sdg_context = build_publication_sdg_context(publications)
    sdg_context["sdg_featured"] = select_spread_sdg_preview(sdg_context["sdg_summary"])

    return render(
        request,
        'publications/list.html',
        {
            'publications': publications,
            'tree_layouts': tree_layouts,
            'admin_preview': admin_preview,
            'initial_preset': initial_preset,
            **sdg_context,
        },
    )


def publication_detail(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    sdg_detail = [
        {
            "number": number,
            "label": SDG_LOOKUP[number]["label"],
        }
        for number in publication.sdg_goal_numbers()
        if number in SDG_LOOKUP
    ]
    return render(
        request,
        'publications/detail.html',
        {
            'publication': publication,
            'sdg_detail': sdg_detail,
        },
    )


@staff_member_required
def publication_tree_editor(request, pk):
    tree_layout = get_object_or_404(PublicationTreeLayout, pk=pk)

    if request.method == "POST":
        form = PublicationTreeLayoutForm(request.POST, instance=tree_layout)
        if form.is_valid():
            tree_layout = form.save()
            messages.success(request, "Tree layout saved.")
            return redirect("publications:tree_editor", pk=tree_layout.pk)
    else:
        form = PublicationTreeLayoutForm(instance=tree_layout)

    sdg_context = build_publication_sdg_context(Publication.objects.all())
    sdg_context["sdg_featured"] = select_spread_sdg_preview(sdg_context["sdg_summary"])
    tree_layouts = {
        layout.preset_key: layout.as_frontend_config()
        for layout in PublicationTreeLayout.objects.filter(is_active=True)
    }
    tree_layouts[tree_layout.preset_key] = tree_layout.as_frontend_config()

    return render(
        request,
        "publications/tree_editor.html",
        {
            "form": form,
            "tree_layout": tree_layout,
            "tree_layouts": tree_layouts,
            "initial_preset": tree_layout.preset_key,
            **sdg_context,
        },
    )
