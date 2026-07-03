"""
App: quizzes
Système d'évaluation automatique : un quiz optionnel par module,
avec questions à choix multiples et correction automatique.
"""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Quiz(models.Model):
    titre = models.CharField(max_length=200)
    note_passage = models.PositiveIntegerField(
        default=60,
        help_text="Pourcentage minimum requis pour valider le quiz (0-100).",
    )
    module = models.OneToOneField(
        "courses.Module",
        on_delete=models.CASCADE,
        related_name="quiz",
    )

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quiz"

    def __str__(self):
        return f"Quiz — {self.module.titre}"

    def clean(self):
        if not (0 <= self.note_passage <= 100):
            raise ValidationError("La note de passage doit être comprise entre 0 et 100.")


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    enonce = models.TextField()
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["quiz", "ordre"]

    def __str__(self):
        return self.enonce[:60]


class ReponseOption(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    texte = models.CharField(max_length=300)
    est_correcte = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Option de réponse"
        verbose_name_plural = "Options de réponse"

    def __str__(self):
        marque = "✓" if self.est_correcte else "✗"
        return f"[{marque}] {self.texte}"


class TentativeQuiz(models.Model):
    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tentatives_quiz",
        limit_choices_to={"role": "etudiant"},
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="tentatives"
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    reussi = models.BooleanField(default=False)
    date_tentative = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tentative de quiz"
        verbose_name_plural = "Tentatives de quiz"
        ordering = ["-date_tentative"]

    def __str__(self):
        return f"{self.etudiant} — {self.quiz} : {self.score}%"

    @classmethod
    def corriger_et_creer(cls, etudiant, quiz, reponses_selectionnees):
        """
        Corrige automatiquement une tentative de quiz.

        reponses_selectionnees : dict { question_id: option_id_choisie }
        Retourne l'objet TentativeQuiz créé, avec le score calculé.
        """
        questions = quiz.questions.all()
        total = questions.count()
        if total == 0:
            score = Decimal("0.00")
        else:
            bonnes_reponses = 0
            for question in questions:
                option_choisie_id = reponses_selectionnees.get(question.id)
                if option_choisie_id and question.options.filter(
                    id=option_choisie_id, est_correcte=True
                ).exists():
                    bonnes_reponses += 1
            score = (Decimal(bonnes_reponses) / Decimal(total)) * Decimal(100)

        tentative = cls.objects.create(
            etudiant=etudiant,
            quiz=quiz,
            score=score.quantize(Decimal("0.01")),
            reussi=score >= quiz.note_passage,
        )
        return tentative