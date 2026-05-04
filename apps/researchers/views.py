from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Researcher


ORG_CHART_SLOTS = [
    {
        "key": "executive",
        "label": "Executive",
        "description": "Center leadership and executive coordination",
        "theme": "executive",
        "aliases": ["executive"],
    },
    {
        "key": "business-intelligence",
        "label": "Business Intelligence",
        "description": "Research unit",
        "theme": "team",
        "aliases": ["business intelligence", "business-intelligence", "bi"],
    },
    {
        "key": "innovation-and-ai",
        "label": "Innovation and AI",
        "description": "Research unit",
        "theme": "team",
        "aliases": ["innovation and ai", "innovation & ai", "ai", "innovation"],
    },
    {
        "key": "social-relations-and-assessment",
        "label": "Social Relations and Assessment",
        "description": "Research unit",
        "theme": "team",
        "aliases": [
            "social relations and assessment",
            "social relations & assessment",
            "social assessment",
        ],
    },
    {
        "key": "support",
        "label": "Support",
        "description": "Support layer connecting technical and part-time teams to the research units above",
        "theme": "support",
        "aliases": ["support"],
    },
    {
        "key": "technical-and-architects",
        "label": "Technical & Architects",
        "description": "Technical support unit",
        "theme": "support",
        "aliases": ["technical & architects", "technical and architects", "technical", "architects"],
    },
    {
        "key": "part-time",
        "label": "Part-time Researchers",
        "description": "Researchers currently studying or contributing part-time",
        "theme": "support",
        "aliases": ["part-time researchers", "part time researchers", "part-time"],
    },
    {
        "key": "unassigned",
        "label": "Unassigned Team",
        "description": "Researchers whose team name does not match a predefined organization slot yet",
        "theme": "support",
        "aliases": [],
    },
]


def normalize_team_name(value):
    return " ".join((value or "").strip().lower().replace("&", " and ").replace("-", " ").split())


def build_researcher_payload(researcher):
    expertise_items = [
        item.strip()
        for item in (researcher.expertise or "").replace("\n", ",").split(",")
        if item.strip()
    ]
    return {
        "id": researcher.pk,
        "name": researcher.profile_label,
        "full_name": researcher.full_name,
        "role": researcher.get_organization_role_display(),
        "position": researcher.position,
        "team_name": researcher.team_name,
        "academic_status": researcher.academic_status,
        "expertise": researcher.expertise,
        "expertise_items": expertise_items,
        "bio": researcher.bio,
        "email": researcher.email,
        "phone": researcher.phone,
        "image_url": researcher.profile_image.url if researcher.profile_image else "",
        "profile_url": reverse("researchers:detail", args=[researcher.pk]),
    }


def researcher_list(request):
    researchers = Researcher.objects.filter(is_active=True)
    executives = []
    team_map = {}
    part_time_researchers = []

    executive_roles = {
        Researcher.OrganizationRole.DIRECTOR,
        Researcher.OrganizationRole.DEPUTY_DIRECTOR,
        Researcher.OrganizationRole.SECRETARY,
    }
    research_roles = {
        Researcher.OrganizationRole.TEAM_LEAD,
        Researcher.OrganizationRole.RESEARCHER,
    }

    for researcher in researchers:
        if researcher.organization_role in executive_roles:
            executives.append(researcher)
        elif researcher.organization_role == Researcher.OrganizationRole.PART_TIME_RESEARCHER:
            part_time_researchers.append(researcher)
        elif researcher.organization_role in research_roles:
            team_name = researcher.team_name or "Research Team"
            team_map.setdefault(team_name, []).append(researcher)

    ordered_team_map = {}
    for team_name, members in team_map.items():
        ordered_team_map[team_name] = sorted(
            members,
            key=lambda member: (
                0 if member.organization_role == Researcher.OrganizationRole.TEAM_LEAD else 1,
                member.display_order,
                member.full_name,
            ),
        )

    slot_members = {slot["key"]: [] for slot in ORG_CHART_SLOTS}
    slot_members["executive"] = sorted(executives, key=lambda member: (member.display_order, member.full_name))
    slot_members["part-time"] = sorted(part_time_researchers, key=lambda member: (member.display_order, member.full_name))

    alias_slot_map = {}
    for slot in ORG_CHART_SLOTS:
        for alias in slot["aliases"]:
            alias_slot_map[normalize_team_name(alias)] = slot["key"]

    for team_name, members in ordered_team_map.items():
        normalized_name = normalize_team_name(team_name)
        matched_slot = alias_slot_map.get(normalized_name)
        if matched_slot:
            slot_members[matched_slot].extend(members)
        else:
            slot_members["unassigned"].extend(members)

    researcher_groups = []
    for slot in ORG_CHART_SLOTS:
        members = slot_members.get(slot["key"], [])
        researcher_groups.append(
            {
                "key": slot["key"],
                "label": slot["label"],
                "description": slot["description"],
                "theme": slot["theme"],
                "members": [build_researcher_payload(member) for member in members],
                "count": len(members),
                "interactive": slot["key"] != "support",
            }
        )

    chart_lookup = {group["key"]: group for group in researcher_groups}
    org_chart = {
        "executive": chart_lookup["executive"],
        "top_teams": [
            chart_lookup["business-intelligence"],
            chart_lookup["innovation-and-ai"],
            chart_lookup["social-relations-and-assessment"],
        ],
        "support": chart_lookup["support"],
        "bottom_teams": [
            chart_lookup["technical-and-architects"],
            chart_lookup["part-time"],
        ],
    }
    unit_count = sum(
        1
        for group in researcher_groups
        if group["key"] not in {"executive"}
        and group["count"] > 0
    )

    return render(
        request,
        'researchers/list.html',
        {
            'researchers': researchers,
            'executives': executives,
            'part_time_researchers': part_time_researchers,
            'researcher_groups': researcher_groups,
            'org_chart': org_chart,
            'unit_count': unit_count,
        },
    )


def researcher_detail(request, pk):
    researcher = get_object_or_404(Researcher, pk=pk, is_active=True)
    return render(
        request,
        'researchers/detail.html',
        {'researcher': researcher},
    )

# Create your views here.
