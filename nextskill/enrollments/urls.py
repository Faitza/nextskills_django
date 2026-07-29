from django.urls import path

from . import views

app_name = "enrollments"  # espace de noms, permet d'écrire {% url 'enrollments:mes_cours' %} dans les templates

urlpatterns = [
    path("mon-apprentissage/", views.mes_cours, name="mes_cours"),  # tableau de bord étudiant
    path("mon-apprentissage/certificat/<int:inscription_id>/apercu/", views.apercu_certificat, name="apercu_certificat"),  # page d'aperçu avant téléchargement
    path("mon-apprentissage/certificat/<int:inscription_id>/image/", views.image_certificat, name="image_certificat"),  # image PNG du PDF réel (utilisée par la page d'aperçu)
    path("mon-apprentissage/certificat/<int:inscription_id>/", views.certificat, name="certificat"),  # téléchargement du PDF
]