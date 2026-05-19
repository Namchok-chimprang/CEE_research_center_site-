from pathlib import Path
import re

from django.conf import settings
from django.db.models import Count, Prefetch, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import ProjectCategory, ResearchProject


def project_list(request):
    projects = ResearchProject.objects.filter(is_published=True)

    selected_year = request.GET.get("year", "").strip()
    selected_status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()

    if selected_year.isdigit():
        projects = projects.filter(fiscal_year=int(selected_year))
    else:
        selected_year = ""

    valid_statuses = {choice for choice, _ in ResearchProject.Status.choices}
    if selected_status in valid_statuses:
        projects = projects.filter(status=selected_status)
    else:
        selected_status = ""

    if query:
        projects = projects.filter(title__icontains=query)

    ongoing_projects = projects.filter(status=ResearchProject.Status.ONGOING)
    completed_projects = projects.filter(status=ResearchProject.Status.COMPLETED)

    totals = ResearchProject.objects.filter(is_published=True).aggregate(total_projects=Count("id"))
    overall_ongoing = ResearchProject.objects.filter(
        is_published=True,
        status=ResearchProject.Status.ONGOING,
    ).count()
    overall_completed = ResearchProject.objects.filter(
        is_published=True,
        status=ResearchProject.Status.COMPLETED,
    ).count()
    overall_budget = ResearchProject.objects.filter(is_published=True).aggregate(total=Sum("budget_amount"))["total"]

    featured_projects = ResearchProject.objects.filter(is_published=True, is_featured=True)[:3]
    available_years = (
        ResearchProject.objects.filter(is_published=True)
        .values_list("fiscal_year", flat=True)
        .distinct()
        .order_by("-fiscal_year")
    )

    context = {
        "ongoing_projects": ongoing_projects,
        "completed_projects": completed_projects,
        "featured_projects": featured_projects,
        "available_years": available_years,
        "selected_year": selected_year,
        "selected_status": selected_status,
        "search_query": query,
        "status_choices": ResearchProject.Status.choices,
        "summary_total_projects": totals["total_projects"] or 0,
        "summary_ongoing_projects": overall_ongoing,
        "summary_completed_projects": overall_completed,
        "summary_total_budget": overall_budget or 0,
    }
    return render(request, "projects/list.html", context)


def project_detail(request, slug):
    project = get_object_or_404(ResearchProject, slug=slug, is_published=True)
    return render(request, "projects/detail.html", {"project": project})


def city_map(request):
    categories = (
        ProjectCategory.objects.filter(is_active=True)
        .annotate(project_count=Count("projects", filter=Q(projects__is_published=True)))
        .order_by("display_order", "name")
    )
    return render(request, "projects/city.html", {"categories": categories})

def _svg_placement_from_static(static_rel_path):
    static_path = Path(settings.BASE_DIR) / "static" / static_rel_path
    if not static_path.exists():
        return None

    content = static_path.read_text(encoding="utf-8", errors="ignore")
    svg_tag_end = content.find(">")
    svg_head = content[:svg_tag_end] if svg_tag_end != -1 else content

    viewbox_match = re.search(r'viewBox\s*=\s*"([^"]+)"', svg_head)
    if not viewbox_match:
        return None

    parts = viewbox_match.group(1).strip().split()
    if len(parts) != 4:
        return None

    try:
        svg_w = float(parts[2])
        svg_h = float(parts[3])
    except ValueError:
        return None

    # Building SVGs are exported from a 1536x1024 base map and include a full-canvas
    # rect translated by x/y. We recover original center position from that offset.
    rect_match = re.search(
        r"<rect[^>]*\bx\s*=\s*\"([\-0-9.]+)\"[^>]*\by\s*=\s*\"([\-0-9.]+)\"[^>]*\bwidth\s*=\s*\"([0-9.]+)\"[^>]*\bheight\s*=\s*\"([0-9.]+)\"",
        content,
    )
    if not rect_match:
        return None

    try:
        rect_x = float(rect_match.group(1))
        rect_y = float(rect_match.group(2))
        canvas_w = float(rect_match.group(3))
        canvas_h = float(rect_match.group(4))
    except ValueError:
        return None

    if canvas_w <= 0 or canvas_h <= 0:
        return None

    center_x = ((-rect_x) + (svg_w / 2.0)) / canvas_w * 100.0
    center_y = ((-rect_y) + (svg_h / 2.0)) / canvas_h * 100.0
    width_pct = (svg_w / canvas_w) * 100.0
    height_pct = (svg_h / canvas_h) * 100.0

    return {
        "center_x": center_x,
        "center_y": center_y,
        "width_pct": width_pct,
        "height_pct": height_pct,
    }


def city_map_alt(request):
    categories = list(
        ProjectCategory.objects.filter(is_active=True)
        .annotate(project_count=Count("projects", filter=Q(projects__is_published=True)))
        .order_by("display_order", "name")
    )

    # Support the current seeded category slugs and keep legacy keys for compatibility.
    building_map = {
        "smart-agriculture-future-food": "images/city-buildings/food-loss-building.svg",
        "energy-environment-sustainability": "images/city-buildings/energy-building.svg",
        "ai-digital-intelligent-technology": "images/city-buildings/ai-building.svg",
        "economy-finance-forecasting": "images/city-buildings/cee-city.svg",
        "health-society-wellbeing": "images/city-buildings/health-building.svg",
        "water-regional-environment-management": "images/city-buildings/water-building.svg",
        "policy-science-institutional-development": "images/city-buildings/sci-building.svg",
        "community-economy-high-value-supply-chain": "images/city-buildings/community-area.svg",
        "impact-assessment-public-policy": "images/city-buildings/se-area.svg",
        "data-infrastructure-smart-city": "images/city-buildings/data-research.svg",
        "ai-digital-analytics": "images/city-buildings/ai-building.svg",
        "agriculture-food": "images/city-buildings/food-loss-building.svg",
        "community-social": "images/city-buildings/community-area.svg",
        "economy-policy": "images/city-buildings/cee-city.svg",
        "energy-environment": "images/city-buildings/energy-building.svg",
        "health-wellbeing": "images/city-buildings/health-building.svg",
        "water-management-climate-adaptation": "images/city-buildings/water-building.svg",
        "science-technology-innovation-policy": "images/city-buildings/sci-building.svg",
        "fund-management-financial-evaluation": "images/city-buildings/hight-building.svg",
    }

    size_cache = {}
    for category in categories:
        category.building_src = building_map.get(category.slug, "")
        category.building_w = 0
        category.building_h = 0
        category.building_x = category.map_x
        category.building_y = category.map_y

        if not category.building_src:
            continue

        if category.building_src not in size_cache:
            size_cache[category.building_src] = _svg_placement_from_static(category.building_src)

        placement = size_cache[category.building_src]
        if placement:
            category.building_w = placement["width_pct"]
            category.building_h = placement["height_pct"]
            category.building_x = placement["center_x"]
            category.building_y = placement["center_y"]

    # Optional static hover-only building while category/data is not ready yet.
    se_area_placeholder = {
        "slug": "se-area-placeholder",
        "name": "SE Area (Coming Soon)",
        "building_src": "images/city-buildings/se-area.svg",
        "building_x": 20.74,
        "building_y": 27.05,
        "building_w": 41.28,
        "building_h": 34.57,
        "color": "#4b5f78",
    }

    return render(
        request,
        "projects/city_alt.html",
        {
            "categories": categories,
            "se_area_placeholder": se_area_placeholder,
        },
    )


def city_map_data(request):
    published_projects = ResearchProject.objects.filter(is_published=True).order_by("-fiscal_year", "title")
    categories = (
        ProjectCategory.objects.filter(is_active=True)
        .prefetch_related(Prefetch("projects", queryset=published_projects))
        .order_by("display_order", "name")
    )

    payload = []
    for category in categories:
        projects_qs = category.projects.all()
        projects = [
            {
                "title": project.title,
                "slug": project.slug,
                "detail_url": project.get_absolute_url(),
                "status": project.get_status_display(),
                "fiscal_year": project.fiscal_year,
                "funding_source": project.funding_source,
                "principal_investigator": project.principal_investigator,
                "is_featured": project.is_featured,
            }
            for project in projects_qs
        ]

        payload.append(
            {
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "color": category.color,
                "map_x": category.map_x,
                "map_y": category.map_y,
                "icon": category.icon,
                "project_count": len(projects),
                "projects": projects,
            }
        )

    return JsonResponse({"categories": payload})
