"""
App: accounts
Connexion, inscription (étudiant/formateur) et déconnexion.
"""
from django.contrib import messages  # messages flash affichés en haut de page après une action
from django.contrib.auth import login as auth_login  # renommé pour ne pas entrer en conflit avec la vue connexion()
from django.contrib.auth import logout as auth_logout  # renommé pour ne pas entrer en conflit avec la vue deconnexion()
from django.contrib.auth.forms import AuthenticationForm  # formulaire de connexion standard fourni par Django
from django.shortcuts import redirect, render  # raccourcis pour rediriger ou afficher un template
from django.utils.http import url_has_allowed_host_and_scheme  # valide qu'une URL de redirection reste sur le site (sécurité anti open-redirect)

from .forms import InscriptionForm


def _url_suivante(request):
    """Récupère et valide le paramètre ?next=, pour revenir sur la page d'origine après connexion."""
    next_url = request.POST.get("next") or request.GET.get("next")  # présent en POST après soumission, ou en GET au premier chargement
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):  # empêche qu'un lien malveillant redirige vers un site externe après connexion
        return next_url
    return None


def connexion(request):
    if request.user.is_authenticated:
        return redirect("pages:accueil")  # inutile de montrer le formulaire à quelqu'un déjà connecté

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)  # request est requis par ce formulaire pour vérifier les tentatives échouées
        if form.is_valid():
            auth_login(request, form.get_user())  # ouvre la session pour l'utilisateur authentifié
            messages.success(request, f"Content de te revoir, {form.get_user().username} !")
            return redirect(_url_suivante(request) or "pages:accueil")  # retourne à la page d'origine si connu, sinon accueil
    else:
        form = AuthenticationForm(request)  # formulaire vide au premier affichage (GET)
    return render(request, "accounts/login.html", {"form": form, "next": _url_suivante(request)})


def inscription(request):
    if request.user.is_authenticated:
        return redirect("pages:accueil")  # un utilisateur connecté n'a pas besoin de s'inscrire à nouveau

    if request.method == "POST":
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()  # crée le compte (hash du mot de passe + centres d'intérêt gérés dans form.save())
            auth_login(request, user)  # connecte automatiquement l'utilisateur après inscription
            messages.success(request, f"Bienvenue sur NextSkill, {user.username} !")
            return redirect("pages:accueil")
    else:
        form = InscriptionForm()  # formulaire vide au premier affichage (GET)
    return render(request, "accounts/register.html", {"form": form})


def deconnexion(request):
    if request.method == "POST":  # exigé en POST pour éviter qu'un simple lien/GET ne déconnecte l'utilisateur (protection CSRF)
        auth_logout(request)  # vide la session
        messages.success(request, "Tu es déconnecté.")
    return redirect("pages:accueil")
