"""Formulaire de paiement (fictif) — choix du mode uniquement."""
from django import forms

from .models import Paiement


class PaiementForm(forms.Form):
    methode = forms.ChoiceField(
        choices=Paiement.Methode.choices,  # réutilise les mêmes choix que le modèle, évite toute duplication/désynchronisation
        widget=forms.RadioSelect,  # affiché comme des boutons radio, pas une liste déroulante
        initial=Paiement.Methode.MONCASH,  # MonCash présélectionné par défaut
        label="Mode de paiement",
    )
