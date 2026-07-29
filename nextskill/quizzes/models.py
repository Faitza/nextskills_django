"""
App: quizzes
Système d'évaluation automatique : un quiz optionnel par module,
avec questions à choix multiples et correction automatique.
"""
from decimal import Decimal  # pour représenter le score avec précision (évite les erreurs d'arrondi des float)

from django.conf import settings  # pour référencer AUTH_USER_MODEL sans import direct
from django.core.exceptions import ValidationError  # levée quand la note de passage est hors limites
from django.db import models


class Quiz(models.Model):
    titre = models.CharField(max_length=200)
    note_passage = models.PositiveIntegerField(
        default=60,  # 60% par défaut si le formateur ne précise rien
        help_text="Pourcentage minimum requis pour valider le quiz (0-100).",
    )
    module = models.OneToOneField(  # un seul quiz possible par module (pas ForeignKey)
        "courses.Module",  # référence en chaîne pour éviter l'import circulaire quizzes <-> courses
        on_delete=models.CASCADE,  # si le module est supprimé, son quiz l'est aussi
        related_name="quiz",  # permet d'écrire module.quiz
    )

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quiz"  # identique au singulier en français

    def __str__(self):
        return f"Quiz — {self.module.titre}"

    def clean(self):
        # sécurité supplémentaire au niveau modèle, en plus du PositiveIntegerField qui n'empêche pas de dépasser 100
        if not (0 <= self.note_passage <= 100):
            raise ValidationError("La note de passage doit être comprise entre 0 et 100.")


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")  # si le quiz est supprimé, ses questions le sont aussi
    enonce = models.TextField()
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["quiz", "ordre"]  # affichage dans l'ordre pédagogique voulu par le formateur

    def __str__(self):
        return self.enonce[:60]  # tronqué pour rester lisible dans l'admin (l'énoncé peut être long)


class ReponseOption(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"  # si la question est supprimée, ses options le sont aussi
    )
    texte = models.CharField(max_length=300)
    est_correcte = models.BooleanField(default=False)  # une seule option devrait être True par question (non forcé au niveau modèle)

    class Meta:
        verbose_name = "Option de réponse"
        verbose_name_plural = "Options de réponse"

    def __str__(self):
        marque = "✓" if self.est_correcte else "✗"  # repère visuel rapide dans l'admin pour identifier la bonne réponse
        return f"[{marque}] {self.texte}"


class TentativeQuiz(models.Model):
    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # si l'étudiant est supprimé, ses tentatives le sont aussi
        related_name="tentatives_quiz",  # permet d'écrire utilisateur.tentatives_quiz.all()
        limit_choices_to={"role": "etudiant"},  # limite le champ dans l'admin aux comptes étudiant
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="tentatives"  # si le quiz est supprimé, les tentatives associées le sont aussi
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))  # ex: 100.00
    reussi = models.BooleanField(default=False)  # calculé une fois pour toutes à la création, jamais recalculé ensuite
    date_tentative = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tentative de quiz"
        verbose_name_plural = "Tentatives de quiz"
        ordering = ["-date_tentative"]  # les plus récentes en premier (utile pour garder un historique des essais)

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
            score = Decimal("0.00")  # évite une division par zéro si le quiz n'a encore aucune question
        else:
            bonnes_reponses = 0
            for question in questions:
                option_choisie_id = reponses_selectionnees.get(question.id)  # None si l'étudiant n'a pas répondu à cette question
                if option_choisie_id and question.options.filter(
                    id=option_choisie_id, est_correcte=True  # vérifie en base que l'option choisie appartient bien à cette question ET est correcte
                ).exists():
                    bonnes_reponses += 1
            score = (Decimal(bonnes_reponses) / Decimal(total)) * Decimal(100)  # pourcentage de bonnes réponses

        tentative = cls.objects.create(
            etudiant=etudiant,
            quiz=quiz,
            score=score.quantize(Decimal("0.01")),  # arrondit à 2 décimales, ex: 66.666... -> 66.67
            reussi=score >= quiz.note_passage,  # comparé à la note de passage définie par le formateur sur ce quiz
        )
        return tentative
