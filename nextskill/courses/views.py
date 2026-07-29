"""
App: courses
Catalogue public des cours publiés, page de détail, lecture de leçon,
espace formateur (création de cours) et espace administrateur (validation).
"""
from django.contrib import messages  # messages flash affichés en haut de page après une action
from django.contrib.auth import get_user_model  # récupère le modèle utilisateur actif du projet (Utilisateur)
from django.contrib.auth.decorators import login_required  # protège une vue : redirige vers /connexion/ si anonyme
from django.db.models import Avg, Count  # fonctions d'agrégation SQL (moyenne, comptage)
from django.shortcuts import get_object_or_404, redirect, render  # raccourcis Django courants
from django.views.decorators.http import require_POST  # rejette toute requête qui n'est pas un POST

from enrollments.models import Inscription, ProgressionLecon

from .forms import AvisForm, CoursForm, LeconForm, ModuleForm
from .models import Avis, Categorie, Cours, Lecon, Module


def catalogue(request):
    # seuls les cours validés par l'admin doivent apparaître publiquement
    cours_liste = Cours.objects.filter(statut=Cours.Statut.PUBLIE).select_related(
        "categorie", "formateur"  # évite une requête SQL par cours pour afficher sa catégorie/son formateur
    )

    categorie_id = request.GET.get("categorie")  # filtre optionnel passé en paramètre d'URL (?categorie=3)
    if categorie_id:
        cours_liste = cours_liste.filter(categorie_id=categorie_id)

    cours_liste = cours_liste.annotate(note_moyenne=Avg("avis__note"))  # calcule la moyenne des avis en une seule requête SQL

    return render(
        request,
        "courses/catalogue.html",
        {
            "cours_liste": cours_liste,
            "categories": Categorie.objects.all(),  # pour construire les filtres cliquables (chips)
            "categorie_active": categorie_id,  # pour surligner le filtre actuellement sélectionné
        },
    )


def detail_cours(request, slug):
    cours = get_object_or_404(
        Cours.objects.select_related("categorie", "formateur").prefetch_related(
            "modules__lecons", "modules__quiz"  # précharge modules+leçons+quiz en 2 requêtes au lieu d'une par module
        ),
        slug=slug,
        statut=Cours.Statut.PUBLIE,  # un cours non publié renvoie une 404, même pour son propre formateur
    )
    stats = cours.avis.aggregate(note_moyenne=Avg("note"))  # moyenne des notes, None si aucun avis

    inscription = None
    lecons_terminees = set()
    mon_avis = None
    if request.user.is_authenticated and request.user.est_etudiant:
        # ne cherche l'inscription que pour un étudiant connecté ; sinon inscription reste None (cours "verrouillé" dans le template)
        inscription = Inscription.objects.filter(etudiant=request.user, cours=cours).first()
        if inscription:
            # ensemble des ids de leçons déjà terminées, pour afficher un ✓ dans le rail de modules
            lecons_terminees = set(
                ProgressionLecon.objects.filter(
                    etudiant=request.user,
                    lecon__module__cours=cours,
                    statut=ProgressionLecon.Statut.TERMINE,
                ).values_list("lecon_id", flat=True)
            )
            mon_avis = Avis.objects.filter(etudiant=request.user, cours=cours).first()  # None si l'étudiant n'a pas encore laissé d'avis

    return render(
        request,
        "courses/detail.html",
        {
            "cours": cours,
            "avis_liste": cours.avis.select_related("etudiant"),
            "note_moyenne": stats["note_moyenne"],
            "inscription": inscription,
            "lecons_terminees": lecons_terminees,
            "mon_avis": mon_avis,
        },
    )


@login_required  # une leçon n'est accessible qu'à un utilisateur connecté (et inscrit, vérifié plus bas)
def lire_lecon(request, slug, lecon_id):
    cours = get_object_or_404(Cours, slug=slug, statut=Cours.Statut.PUBLIE)
    lecon = get_object_or_404(Lecon, id=lecon_id, module__cours=cours)  # vérifie que la leçon appartient bien à ce cours

    inscription = Inscription.objects.filter(etudiant=request.user, cours=cours).first()
    if not inscription:
        # empêche un utilisateur connecté mais non-inscrit de contourner l'achat en devinant l'URL de la leçon
        messages.error(request, "Tu dois d'abord t'inscrire à ce cours pour accéder à cette leçon.")
        return redirect("courses:detail", slug=slug)

    # crée le suivi de progression au premier accès, le réutilise ensuite
    progression, _ = ProgressionLecon.objects.get_or_create(etudiant=request.user, lecon=lecon)

    if request.method == "POST":  # soumission du bouton "Marquer comme terminée"
        progression.marquer_terminee()  # met aussi à jour Inscription.progression_pourcentage (voir enrollments/models.py)
        messages.success(request, "Leçon marquée comme terminée.")
        return redirect("courses:lecon", slug=slug, lecon_id=lecon_id)  # évite la re-soumission du formulaire au rechargement (POST/redirect/GET)

    return render(
        request,
        "courses/lecon.html",
        {"cours": cours, "lecon": lecon, "progression": progression},
    )


@login_required
def laisser_avis(request, slug):
    """Un étudiant inscrit laisse (ou modifie) son avis 1-5 étoiles sur un cours."""
    cours = get_object_or_404(Cours, slug=slug, statut=Cours.Statut.PUBLIE)

    if not request.user.est_etudiant:
        messages.error(request, "Seuls les étudiants peuvent laisser un avis.")
        return redirect("courses:detail", slug=slug)

    inscription = Inscription.objects.filter(etudiant=request.user, cours=cours).first()
    if not inscription:
        # empêche un utilisateur connecté mais non-inscrit de noter un cours qu'il n'a jamais suivi
        messages.error(request, "Tu dois être inscrit à ce cours pour laisser un avis.")
        return redirect("courses:detail", slug=slug)

    # None si l'étudiant n'a pas encore laissé d'avis ; sinon on modifie l'avis existant
    # (unique_together etudiant+cours empêche de toute façon d'en créer un deuxième)
    avis_existant = Avis.objects.filter(etudiant=request.user, cours=cours).first()

    if request.method == "POST":
        form = AvisForm(request.POST, instance=avis_existant)
        if form.is_valid():
            avis = form.save(commit=False)
            avis.etudiant = request.user
            avis.cours = cours
            avis.save()
            messages.success(request, "Ton avis a été enregistré, merci !")
            return redirect("courses:detail", slug=slug)
    else:
        form = AvisForm(instance=avis_existant)  # pré-rempli si l'étudiant modifie son avis

    return render(
        request,
        "courses/laisser_avis.html",
        {"cours": cours, "form": form, "avis_existant": avis_existant},
    )


@login_required
def tableau_de_bord_formateur(request):
    if not request.user.est_formateur:
        messages.error(request, "Cette page est réservée aux formateurs.")
        return redirect("pages:accueil")

    cours_liste = []
    # boucle volontairement simple (pas d'annotate combiné) pour éviter le piège du
    # produit cartésien Django quand on agrège sur deux relations inversées différentes
    # (inscriptions et avis) dans la même requête : les moyennes seraient faussées.
    for cours in Cours.objects.filter(formateur=request.user).select_related("categorie"):
        progression_moyenne = (
            cours.inscriptions.aggregate(m=Avg("progression_pourcentage"))["m"] or 0  # 0 si aucun inscrit
        )
        note_moyenne = cours.avis.aggregate(m=Avg("note"))["m"]  # None si aucun avis, affiché "—" côté template
        cours_liste.append(
            {
                "cours": cours,
                "nb_inscrits": cours.nombre_inscrits,
                "progression_moyenne": progression_moyenne,
                "note_moyenne": note_moyenne,
            }
        )

    return render(
        request,
        "courses/tableau_de_bord_formateur.html",
        {
            "cours_liste": cours_liste,
            "total_cours": len(cours_liste),
            "total_inscrits": sum(item["nb_inscrits"] for item in cours_liste),
        },
    )


@login_required
def creer_cours(request):
    if not request.user.est_formateur:
        messages.error(request, "Seuls les formateurs peuvent créer des cours.")
        return redirect("pages:accueil")

    if request.method == "POST":
        form = CoursForm(request.POST, request.FILES)  # request.FILES nécessaire pour l'upload de image_couverture
        if form.is_valid():
            cours = form.save(commit=False)  # ne sauvegarde pas encore, il manque formateur/statut
            cours.formateur = request.user  # le cours appartient à celui qui le crée, jamais choisi dans le formulaire
            cours.statut = Cours.Statut.EN_ATTENTE  # jamais publié directement, doit passer par la validation admin
            cours.save()
            messages.success(
                request,
                f"« {cours.titre} » a été soumis pour validation par l'administrateur.",
            )
            return redirect("courses:tableau_de_bord_formateur")
    else:
        form = CoursForm()  # formulaire vide au premier affichage (GET)

    return render(request, "courses/creer_cours.html", {"form": form})


@login_required
def gerer_cours(request, slug):
    """Vue centrale du formateur pour gérer les modules et leçons (vidéo/PDF/texte) d'un de ses cours."""
    # formateur=request.user dans la requête = seul le propriétaire du cours accède à cette page (404 sinon, pas juste un refus)
    cours = get_object_or_404(Cours, slug=slug, formateur=request.user)
    modules = cours.modules.prefetch_related("lecons").all()  # précharge les leçons pour éviter une requête par module
    return render(request, "courses/gerer_cours.html", {"cours": cours, "modules": modules})


@login_required
def ajouter_module(request, slug):
    cours = get_object_or_404(Cours, slug=slug, formateur=request.user)  # même vérification de propriété que gerer_cours

    if request.method == "POST":
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)  # ne sauvegarde pas encore, il manque le cours parent
            module.cours = cours
            module.save()
            messages.success(request, f"Module « {module.titre} » ajouté.")
            return redirect("courses:gerer_cours", slug=slug)
    else:
        form = ModuleForm(initial={"ordre": cours.modules.count()})  # pré-remplit l'ordre suivant logique (0, 1, 2...)

    return render(request, "courses/ajouter_module.html", {"cours": cours, "form": form})


@login_required
def ajouter_lecon(request, slug, module_id):
    cours = get_object_or_404(Cours, slug=slug, formateur=request.user)
    module = get_object_or_404(Module, id=module_id, cours=cours)  # vérifie que le module appartient bien à ce cours

    if request.method == "POST":
        form = LeconForm(request.POST, request.FILES)  # request.FILES nécessaire pour l'upload de vidéo/pdf
        if form.is_valid():
            lecon = form.save(commit=False)  # ne sauvegarde pas encore, il manque le module parent
            lecon.module = module
            lecon.save()
            messages.success(request, f"Leçon « {lecon.titre} » publiée.")
            return redirect("courses:gerer_cours", slug=slug)
    else:
        form = LeconForm(initial={"ordre": module.lecons.count()})  # pré-remplit l'ordre suivant logique

    return render(
        request, "courses/ajouter_lecon.html", {"cours": cours, "module": module, "form": form}
    )


@login_required
@require_POST  # une suppression ne doit jamais se déclencher via un simple lien GET
def supprimer_module(request, slug, module_id):
    cours = get_object_or_404(Cours, slug=slug, formateur=request.user)
    module = get_object_or_404(Module, id=module_id, cours=cours)
    module.delete()  # supprime aussi ses leçons en cascade (on_delete=CASCADE sur Lecon.module)
    messages.success(request, "Module supprimé.")
    return redirect("courses:gerer_cours", slug=slug)


@login_required
@require_POST
def supprimer_lecon(request, slug, lecon_id):
    cours = get_object_or_404(Cours, slug=slug, formateur=request.user)
    lecon = get_object_or_404(Lecon, id=lecon_id, module__cours=cours)  # vérifie que la leçon appartient bien à ce cours
    lecon.delete()
    messages.success(request, "Leçon supprimée.")
    return redirect("courses:gerer_cours", slug=slug)


@login_required
def tableau_de_bord_admin(request):
    if not request.user.is_staff:  # is_staff est fiable (fixé par createsuperuser), contrairement à role qui reste "etudiant" par défaut
        messages.error(request, "Cette page est réservée à l'administration.")
        return redirect("pages:accueil")

    Utilisateur = get_user_model()
    stats = {
        "total_utilisateurs": Utilisateur.objects.count(),
        "cours_publies": Cours.objects.filter(statut=Cours.Statut.PUBLIE).count(),
        "cours_en_attente": Cours.objects.filter(statut=Cours.Statut.EN_ATTENTE).count(),
        "formateurs_actifs": Utilisateur.objects.filter(
            role=Utilisateur.Role.FORMATEUR, is_staff=False  # exclut les comptes admin de la statistique "formateurs"
        ).count(),
    }
    cours_en_attente = Cours.objects.filter(statut=Cours.Statut.EN_ATTENTE).select_related(
        "formateur", "categorie"
    )

    # Formateurs et étudiants sont affichés séparément : un formateur crée des
    # cours, un étudiant peut soit juste avoir un compte, soit suivre un cours
    # (nb_cours_suivis distingue les deux cas dans le template). is_staff=False
    # exclut les comptes admin (ex: le superuser garde role="etudiant" par
    # défaut, createsuperuser ne renseigne pas ce champ personnalisé).
    formateurs_recents = Utilisateur.objects.filter(
        role=Utilisateur.Role.FORMATEUR, is_staff=False
    ).annotate(nb_cours_crees=Count("cours_crees", distinct=True)).order_by("-date_inscription")[:8]  # distinct=True évite le comptage en double via les jointures

    etudiants_recents = Utilisateur.objects.filter(
        role=Utilisateur.Role.ETUDIANT, is_staff=False
    ).annotate(nb_cours_suivis=Count("inscriptions", distinct=True)).order_by("-date_inscription")[:8]

    return render(
        request,
        "courses/tableau_de_bord_admin.html",
        {
            "stats": stats,
            "cours_en_attente": cours_en_attente,
            "formateurs_recents": formateurs_recents,
            "etudiants_recents": etudiants_recents,
        },
    )


@login_required
@require_POST  # une validation/rejet ne doit jamais se déclencher via un simple lien GET
def valider_cours(request, cours_id):
    if not request.user.is_staff:
        messages.error(request, "Cette action est réservée à l'administration.")
        return redirect("pages:accueil")

    cours = get_object_or_404(Cours, id=cours_id)
    cours.statut = Cours.Statut.PUBLIE  # le cours devient immédiatement visible dans le catalogue public
    cours.save(update_fields=["statut"])  # ne réécrit que ce champ, plus efficace qu'un save() complet
    messages.success(request, f"« {cours.titre} » a été publié.")
    return redirect("courses:tableau_de_bord_admin")


@login_required
@require_POST
def rejeter_cours(request, cours_id):
    if not request.user.is_staff:
        messages.error(request, "Cette action est réservée à l'administration.")
        return redirect("pages:accueil")

    cours = get_object_or_404(Cours, id=cours_id)
    cours.statut = Cours.Statut.REJETE
    cours.save(update_fields=["statut"])
    messages.info(request, f"« {cours.titre} » a été rejeté.")
    return redirect("courses:tableau_de_bord_admin")
