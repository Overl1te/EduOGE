from django.urls import path
from . import views

app_name = "eduoge"

urlpatterns = [
    path("", views.home, name="home"),
    path("exercise.html", views.exercise_page, name="exercise_page"),

    path("api/exercise", views.api_generate_exercise, name="api_generate_exercise"),
    path("api/check", views.api_check_answer, name="api_check_answer"),
]
