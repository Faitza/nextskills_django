from django.urls import path  # fonction pour déclarer une route URL -> vue

from . import views

app_name = "accounts"  # espace de noms, permet d'écrire {% url 'accounts:connexion' %} dans les templates

urlpatterns = [
    path("connexion/", views.connexion, name="connexion"),  # affiche et traite le formulaire de connexion
    path("inscription/", views.inscription, name="inscription"),  # affiche et traite le formulaire d'inscription
    path("deconnexion/", views.deconnexion, name="deconnexion"),  # déconnecte l'utilisateur (POST uniquement)
]
