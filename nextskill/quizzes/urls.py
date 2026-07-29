from django.urls import path

from . import views

app_name = "quizzes"  # espace de noms, permet d'écrire {% url 'quizzes:quiz' %} dans les templates

urlpatterns = [
    path("quiz/<int:quiz_id>/", views.passer_quiz, name="quiz"),  # affiche et corrige un quiz donné
]
