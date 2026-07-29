from django.contrib import admin

from .models import Question, Quiz, ReponseOption, TentativeQuiz


class ReponseOptionInline(admin.TabularInline):  # permet d'ajouter/modifier des options directement depuis la page d'une Question
    model = ReponseOption
    extra = 0  # n'affiche pas de ligne vide supplémentaire par défaut


class QuestionInline(admin.TabularInline):  # permet d'ajouter/modifier des questions directement depuis la page d'un Quiz
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("titre", "module", "note_passage")  # colonnes affichées dans la liste
    inlines = [QuestionInline]  # affiche les questions du quiz directement sur cette page


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("enonce", "quiz", "ordre")
    inlines = [ReponseOptionInline]  # affiche les options de la question directement sur cette page


@admin.register(TentativeQuiz)
class TentativeQuizAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "quiz", "score", "reussi", "date_tentative")
    list_filter = ("reussi",)  # filtre dans la barre latérale
    search_fields = ("etudiant__username",)  # active la barre de recherche par nom d'utilisateur
