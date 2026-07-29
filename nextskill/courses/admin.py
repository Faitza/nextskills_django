from django.contrib import admin

from .models import Avis, Categorie, Cours, Lecon, Module


class LeconInline(admin.TabularInline):  # permet d'ajouter/modifier des leçons directement depuis la page d'un Module
    model = Lecon
    extra = 0  # n'affiche pas de ligne vide supplémentaire par défaut


class ModuleInline(admin.TabularInline):  # permet d'ajouter/modifier des modules directement depuis la page d'un Cours
    model = Module
    extra = 0


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom",)  # colonne affichée dans la liste
    search_fields = ("nom",)  # active la barre de recherche par nom


@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ("titre", "formateur", "categorie", "niveau", "prix", "statut", "date_creation")
    list_filter = ("statut", "niveau", "categorie")  # filtres dans la barre latérale
    search_fields = ("titre", "formateur__username")  # recherche sur le titre ou le nom du formateur
    prepopulated_fields = {"slug": ("titre",)}  # remplit automatiquement le slug depuis le titre dans le formulaire admin
    inlines = [ModuleInline]  # affiche les modules du cours directement sur cette page


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("titre", "cours", "ordre")
    list_filter = ("cours",)
    inlines = [LeconInline]  # affiche les leçons du module directement sur cette page


@admin.register(Lecon)
class LeconAdmin(admin.ModelAdmin):
    list_display = ("titre", "module", "type_contenu", "ordre", "duree_minutes")
    list_filter = ("type_contenu",)


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "cours", "note", "date_creation")
    list_filter = ("note",)
    search_fields = ("etudiant__username", "cours__titre")
