"""
App: pages
Page publique de NextSkill (avant connexion) : Accueil, Services,
À propos, Contact. Aucune donnée personnelle affichée ici.
"""
from django.contrib import messages  # message flash affiché après l'envoi du formulaire de contact
from django.shortcuts import redirect, render

from .forms import ContactForm


def accueil(request):
    return render(request, "pages/accueil.html")  # page statique, aucune donnée dynamique à passer au template


def services(request):
    return render(request, "pages/services.html")  # page statique


def apropos(request):
    return render(request, "pages/apropos.html")  # page statique


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # pas de sauvegarde en base ni d'envoi d'email réel : projet académique, contact fictif
            messages.success(
                request,
                "Message envoyé (démonstration) — notre équipe te répond sous 48h.",
            )
            return redirect("pages:contact")  # POST/redirect/GET : évite la re-soumission du formulaire au rechargement
    else:
        form = ContactForm()  # formulaire vide au premier affichage (GET)
    return render(request, "pages/contact.html", {"form": form})
