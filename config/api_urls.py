from django.urls import path

from . import api_views

urlpatterns = [
    path('', api_views.api_index, name='api-index'),
    path('researchers/', api_views.researchers_api, name='api-researchers'),
    path('publications/', api_views.publications_api, name='api-publications'),
    path('news/', api_views.news_api, name='api-news'),
]
