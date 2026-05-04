from django.http import JsonResponse

from apps.news.models import News
from apps.publications.models import Publication
from apps.researchers.models import Researcher


def api_index(request):
    data = {
        'project': 'research_center_site',
        'version': 'v1',
        'endpoints': {
            'researchers': '/api/researchers/',
            'publications': '/api/publications/',
            'news': '/api/news/',
        },
    }
    return JsonResponse(data)


def researchers_api(request):
    researchers = list(
        Researcher.objects.filter(is_active=True).values(
            'id',
            'full_name',
            'title',
            'position',
            'expertise',
            'email',
        )
    )
    return JsonResponse({'count': len(researchers), 'results': researchers})


def publications_api(request):
    publications = list(
        Publication.objects.values(
            'id',
            'title',
            'authors',
            'all_authors',
            'corresponding_author',
            'journal',
            'published_date',
            'keywords',
            'source',
            'doi',
            'issn',
            'scopus_eid',
            'journal_quartile',
            'journal_quartile_basis',
            'citescore',
            'sjr',
            'snip',
            'impact_factor',
            'external_url',
            'is_featured',
        )
    )
    return JsonResponse({'count': len(publications), 'results': publications})


def news_api(request):
    news_items = list(
        News.objects.filter(is_published=True).values(
            'id',
            'title',
            'slug',
            'summary',
            'published_at',
        )
    )
    return JsonResponse({'count': len(news_items), 'results': news_items})
