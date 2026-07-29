"""
App: orders
Panier, retrait de ligne, et paiement fictif (checkout panier ou achat direct).
"""
from django.contrib import messages  # messages flash affichés en haut de page après une action
from django.contrib.auth.decorators import login_required  # protège une vue : redirige vers /connexion/ si anonyme
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST  # rejette toute requête qui n'est pas un POST

from courses.models import Cours

from .forms import PaiementForm
from .models import LignePanier, Paiement, Panier


def _refuser_si_pas_etudiant(request):
    """Seuls les étudiants achètent des cours (formateurs/admins exclus)."""
    if not request.user.est_etudiant:
        messages.error(request, "Seuls les comptes étudiants peuvent acheter des cours.")
        return True  # indique à l'appelant qu'il doit rediriger
    return False


@login_required
def voir_panier(request):
    if _refuser_si_pas_etudiant(request):
        return redirect("courses:catalogue")
    panier, _ = Panier.objects.get_or_create(etudiant=request.user)  # crée le panier au premier accès si besoin
    return render(request, "orders/panier.html", {"panier": panier})


@login_required
@require_POST  # ajouter au panier modifie l'état, ne doit jamais se déclencher via un simple lien GET
def ajouter_au_panier(request, slug):
    if _refuser_si_pas_etudiant(request):
        return redirect("courses:detail", slug=slug)

    cours = get_object_or_404(Cours, slug=slug, statut=Cours.Statut.PUBLIE)  # impossible d'ajouter un cours non publié
    panier, _ = Panier.objects.get_or_create(etudiant=request.user)
    _, created = LignePanier.objects.get_or_create(panier=panier, cours=cours)  # ne crée pas de doublon si déjà présent
    if created:
        messages.success(request, f"« {cours.titre} » ajouté à ton panier.")
    else:
        messages.info(request, f"« {cours.titre} » est déjà dans ton panier.")
    return redirect("courses:detail", slug=slug)


@login_required
@require_POST
def retirer_du_panier(request, ligne_id):
    # panier__etudiant=request.user garantit qu'un étudiant ne peut retirer que ses propres lignes
    ligne = get_object_or_404(LignePanier, id=ligne_id, panier__etudiant=request.user)
    ligne.delete()
    return redirect("orders:panier")


@login_required
def paiement_panier(request):
    if _refuser_si_pas_etudiant(request):
        return redirect("courses:catalogue")

    panier, _ = Panier.objects.get_or_create(etudiant=request.user)
    if not panier.lignes.exists():
        messages.info(request, "Ton panier est vide.")
        return redirect("orders:panier")  # rien à payer, inutile d'afficher le formulaire de paiement

    if request.method == "POST":
        form = PaiementForm(request.POST)
        if form.is_valid():
            cours_liste = [ligne.cours for ligne in panier.lignes.select_related("cours")]  # capture le contenu du panier avant paiement
            paiement = Paiement.objects.create(
                etudiant=request.user,
                montant=panier.montant_total,
                methode=form.cleaned_data["methode"],
            )
            paiement.cours.set(cours_liste)  # associe tous les cours du panier à ce paiement (relation M2M)
            paiement.valider()  # simule la réussite : crée les inscriptions et vide le panier
            messages.success(
                request, "Paiement effectué (fictif) — tu as maintenant accès à tes cours."
            )
            return redirect("courses:catalogue")
    else:
        form = PaiementForm()  # formulaire vide au premier affichage (GET)

    return render(
        request,
        "orders/paiement.html",
        {"form": form, "panier": panier, "montant": panier.montant_total},
    )


@login_required
def acheter_direct(request, slug):
    if _refuser_si_pas_etudiant(request):
        return redirect("courses:detail", slug=slug)

    cours = get_object_or_404(Cours, slug=slug, statut=Cours.Statut.PUBLIE)  # impossible d'acheter un cours non publié

    if request.method == "POST":
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = Paiement.objects.create(
                etudiant=request.user,
                montant=cours.prix,
                methode=form.cleaned_data["methode"],
            )
            paiement.cours.set([cours])  # un seul cours associé à ce paiement, contrairement au checkout panier
            paiement.valider()  # simule la réussite : crée l'inscription, retire ce cours du panier s'il y était
            messages.success(
                request,
                f"Paiement effectué (fictif) — tu as maintenant accès à « {cours.titre} ».",
            )
            return redirect("courses:detail", slug=slug)
    else:
        form = PaiementForm()  # formulaire vide au premier affichage (GET)

    return render(
        request,
        "orders/paiement.html",
        {"form": form, "cours_unique": cours, "montant": cours.prix},
    )
