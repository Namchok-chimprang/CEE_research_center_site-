from django.shortcuts import render

from apps.news.models import News
from apps.publications.models import Publication
from apps.researchers.models import Researcher


def home(request):
    context = {
        'researcher_count': Researcher.objects.filter(is_active=True).count(),
        'publication_count': Publication.objects.count(),
        'news_count': News.objects.filter(is_published=True).count(),
        'featured_publications': Publication.objects.filter(is_featured=True)[:3],
        'latest_news': News.objects.filter(is_published=True)[:3],
        'featured_researchers': Researcher.objects.filter(is_active=True)[:3],
    }
    return render(request, 'core/home.html', context)


def about(request):
    return render(request, 'core/about.html')

# Create your views here.
