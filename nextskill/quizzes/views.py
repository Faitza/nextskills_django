"""
App: quizzes
Passage d'un quiz par un étudiant inscrit, avec correction automatique.
"""
from django.contrib import messages  # messages flash affichés en haut de page après une action
from django.contrib.auth.decorators import login_required  # protège la vue : redirige vers /connexion/ si anonyme
from django.shortcuts import get_object_or_404, redirect, render

from enrollments.models import Inscription

from .models import Quiz, TentativeQuiz


@login_required
def passer_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.select_related("module__cours"), id=quiz_id)  # évite 2 requêtes SQL supplémentaires pour remonter jusqu'au cours
    cours = quiz.module.cours

    inscription = Inscription.objects.filter(etudiant=request.user, cours=cours).first()
    if not inscription:
        # empêche un utilisateur connecté mais non-inscrit de contourner l'achat en devinant l'URL du quiz
        messages.error(request, "Tu dois d'abord t'inscrire à ce cours pour passer ce quiz.")
        return redirect("courses:detail", slug=cours.slug)

    if request.method == "POST":  # soumission du formulaire de réponses
        reponses = {}
        for question in quiz.questions.all():
            option_id = request.POST.get(f"question_{question.id}")  # nom de champ défini dans le template quiz.html
            if option_id:
                reponses[question.id] = int(option_id)  # construit le dict {question_id: option_id} attendu par corriger_et_creer
        tentative = TentativeQuiz.corriger_et_creer(request.user, quiz, reponses)  # calcule le score et enregistre la tentative
        return render(
            request, "quizzes/resultat.html", {"quiz": quiz, "tentative": tentative, "cours": cours}
        )

    return render(request, "quizzes/quiz.html", {"quiz": quiz, "cours": cours})  # premier affichage (GET) : formulaire vide
