from django.contrib import admin  # module d'administration Django
from django.contrib.auth.admin import UserAdmin  # configuration d'admin standard pour un modèle utilisateur

from .models import CentreInteret, Utilisateur


@admin.register(Utilisateur)  # enregistre Utilisateur dans /admin/ avec la configuration ci-dessous
class UtilisateurAdmin(UserAdmin):  # hérite de UserAdmin pour garder la gestion mot de passe/permissions native
    list_display = ("username", "email", "role", "specialite", "is_staff", "date_inscription")  # colonnes affichées dans la liste
    list_filter = ("role", "is_staff", "is_active")  # filtres disponibles dans la barre latérale
    fieldsets = UserAdmin.fieldsets + (  # ajoute une section aux champs déjà proposés par UserAdmin (username, password, permissions...)
        ("Informations NextSkill", {"fields": ("role", "photo_profil", "bio", "specialite")}),
    )


@admin.register(CentreInteret)
class CentreInteretAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "categorie")  # colonnes affichées dans la liste
    list_filter = ("categorie",)  # filtre par catégorie dans la barre latérale
    search_fields = ("etudiant__username",)  # active la barre de recherche par nom d'utilisateur de l'étudiant
