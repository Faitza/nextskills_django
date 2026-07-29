from django.contrib import admin

from .models import Inscription, ProgressionLecon


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "cours", "statut", "progression_pourcentage", "date_inscription")  # colonnes affichées dans la liste
    list_filter = ("statut",)  # filtre dans la barre latérale
    search_fields = ("etudiant__username", "cours__titre")  # recherche sur le nom d'utilisateur ou le titre du cours


@admin.register(ProgressionLecon)
class ProgressionLeconAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "lecon", "statut", "date_completion")
    list_filter = ("statut",)
    search_fields = ("etudiant__username",)
