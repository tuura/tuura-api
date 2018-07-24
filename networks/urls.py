from django.urls import path

from . import views

urlpatterns = [
    path('results', views.results, name='results'),
    path('jobs', views.jobs, name='jobs'),
]
