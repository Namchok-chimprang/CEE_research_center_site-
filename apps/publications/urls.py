from django.urls import path

from . import views

app_name = 'publications'

urlpatterns = [
    path('', views.publication_list, name='list'),
    path('tree-editor/<int:pk>/', views.publication_tree_editor, name='tree_editor'),
    path('<int:pk>/', views.publication_detail, name='detail'),
]
