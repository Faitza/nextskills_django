"""Formulaire de la page Contact — pas de sauvegarde en base, message fictif."""
from django import forms


class ContactForm(forms.Form):
    nom = forms.CharField(max_length=100, label="Nom")
    email = forms.EmailField(label="Email")  # valide automatiquement le format de l'adresse
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), label="Message")  # zone de texte plus grande que le CharField par défaut
