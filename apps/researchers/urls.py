from django.urls import path

from . import views

app_name = 'researchers'

urlpatterns = [
    path('', views.researcher_list, name='list'),
    path('<int:pk>/', views.researcher_detail, name='detail'),
]
