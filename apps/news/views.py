from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import News


def news_list(request):
    base_items = News.objects.filter(is_published=True)
    query = request.GET.get("q", "").strip()
    selected_year = request.GET.get("year", "").strip()

    items = base_items
    if query:
        items = items.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        )

    if selected_year.isdigit():
        items = items.filter(published_at__year=int(selected_year))
    else:
        selected_year = ""

    featured_news = items.first()
    regular_items = items[1:] if featured_news else items

    paginator = Paginator(regular_items, 6)
    page_obj = paginator.get_page(request.GET.get("page"))

    year_values = (
        base_items.exclude(published_at__isnull=True)
        .dates("published_at", "year", order="DESC")
    )
    available_years = [value.year for value in year_values]

    return render(
        request,
        "news/list.html",
        {
            "featured_news": featured_news,
            "news_items": page_obj.object_list,
            "page_obj": page_obj,
            "query": query,
            "selected_year": selected_year,
            "available_years": available_years,
        },
    )


def news_detail(request, slug):
    news_item = get_object_or_404(News, slug=slug, is_published=True)
    related_items = (
        News.objects.filter(is_published=True)
        .exclude(pk=news_item.pk)[:3]
    )
    return render(
        request,
        "news/detail.html",
        {
            "news_item": news_item,
            "related_items": related_items,
        },
    )

# Create your views here.
