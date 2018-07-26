from django.urls import path

from . import views

urlpatterns = [
    path('jobs', views.Jobs.as_view()),
    path('jobs/<str:job_id>', views.Jobs.as_view()),
]
