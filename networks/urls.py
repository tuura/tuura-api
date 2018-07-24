from django.urls import path

from . import views

urlpatterns = [
    path('jobs', views.Jobs.as_view())
]
