from django.urls import path

from . import views

app_name = "orders"  # espace de noms, permet d'écrire {% url 'orders:panier' %} dans les templates

urlpatterns = [
    path("panier/", views.voir_panier, name="panier"),  # affiche le contenu du panier
    path("panier/paiement/", views.paiement_panier, name="paiement_panier"),  # paiement fictif de tout le panier
    path("panier/retirer/<int:ligne_id>/", views.retirer_du_panier, name="retirer_du_panier"),  # retire une ligne précise du panier
    path("cours/<slug:slug>/ajouter-au-panier/", views.ajouter_au_panier, name="ajouter_au_panier"),
    path("cours/<slug:slug>/acheter/", views.acheter_direct, name="acheter_direct"),  # achat direct, sans passer par le panier
]
