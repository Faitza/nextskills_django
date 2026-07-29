from django.contrib import admin

from .models import LignePanier, Paiement, Panier


class LignePanierInline(admin.TabularInline):  # permet de voir/modifier les lignes directement depuis la page d'un Panier
    model = LignePanier
    extra = 0  # n'affiche pas de ligne vide supplémentaire par défaut


@admin.register(Panier)
class PanierAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "montant_total", "date_creation")  # colonnes affichées dans la liste (montant_total = property du modèle)
    search_fields = ("etudiant__username",)  # active la barre de recherche par nom d'utilisateur
    inlines = [LignePanierInline]  # affiche les lignes du panier directement sur cette page


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "montant", "methode", "statut", "reference_transaction", "date_paiement")
    list_filter = ("methode", "statut")  # filtres dans la barre latérale
    search_fields = ("etudiant__username", "reference_transaction")  # recherche sur le nom d'utilisateur ou la référence
    filter_horizontal = ("cours",)  # widget à double liste, plus pratique qu'une liste déroulante pour une relation ManyToMany
