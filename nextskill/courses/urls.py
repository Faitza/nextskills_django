from django.urls import path

from . import views

app_name = "courses"  # espace de noms, permet d'écrire {% url 'courses:catalogue' %} dans les templates

urlpatterns = [
    path("catalogue/", views.catalogue, name="catalogue"),  # liste publique des cours publiés
    path("cours/<slug:slug>/", views.detail_cours, name="detail"),  # fiche détaillée d'un cours
    path("cours/<slug:slug>/lecon/<int:lecon_id>/", views.lire_lecon, name="lecon"),  # lecteur de leçon (réservé aux inscrits)
    path("cours/<slug:slug>/avis/", views.laisser_avis, name="laisser_avis"),  # laisser/modifier son avis (réservé aux inscrits)
    path("formateur/tableau-de-bord/", views.tableau_de_bord_formateur, name="tableau_de_bord_formateur"),  # vue d'ensemble des cours du formateur
    path("formateur/creer-cours/", views.creer_cours, name="creer_cours"),  # formulaire de création de cours
    path("formateur/cours/<slug:slug>/gerer/", views.gerer_cours, name="gerer_cours"),  # gestion des modules/leçons d'un cours
    path("formateur/cours/<slug:slug>/module/ajouter/", views.ajouter_module, name="ajouter_module"),
    path(
        "formateur/cours/<slug:slug>/module/<int:module_id>/lecon/ajouter/",
        views.ajouter_lecon,
        name="ajouter_lecon",
    ),
    path(
        "formateur/cours/<slug:slug>/module/<int:module_id>/supprimer/",
        views.supprimer_module,
        name="supprimer_module",
    ),
    path(
        "formateur/cours/<slug:slug>/lecon/<int:lecon_id>/supprimer/",
        views.supprimer_lecon,
        name="supprimer_lecon",
    ),
    path("admin-plateforme/tableau-de-bord/", views.tableau_de_bord_admin, name="tableau_de_bord_admin"),  # préfixé "admin-plateforme" pour ne pas entrer en conflit avec /admin/ (Django admin natif)
    path("admin-plateforme/cours/<int:cours_id>/valider/", views.valider_cours, name="valider_cours"),
    path("admin-plateforme/cours/<int:cours_id>/rejeter/", views.rejeter_cours, name="rejeter_cours"),
]
