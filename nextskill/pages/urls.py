from django.urls import path

from . import views

app_name = "pages"  # espace de noms, permet d'écrire {% url 'pages:accueil' %} dans les templates

urlpatterns = [
    path("", views.accueil, name="accueil"),  # page d'accueil, à la racine du site
    path("services/", views.services, name="services"),
    path("a-propos/", views.apropos, name="apropos"),
    path("contact/", views.contact, name="contact"),
]
