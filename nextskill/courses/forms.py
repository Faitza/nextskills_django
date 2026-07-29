"""Formulaires de gestion des cours par un formateur : cours, modules, leçons.
Contient aussi le formulaire d'avis (note + commentaire) laissé par un étudiant."""
from django import forms

from .models import Avis, Cours, Lecon, Module


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ["titre", "description", "categorie", "niveau", "langue", "prix", "image_couverture"]  # statut/formateur/slug gérés par la vue, pas par le formateur
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),  # zone de texte plus grande que le CharField par défaut
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["titre", "ordre"]  # le cours parent est assigné dans la vue, pas dans le formulaire


class LeconForm(forms.ModelForm):
    class Meta:
        model = Lecon
        fields = ["titre", "type_contenu", "fichier", "contenu_texte", "duree_minutes", "ordre"]  # le module parent est assigné dans la vue
        widgets = {
            "contenu_texte": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()  # récupère les données déjà validées champ par champ
        type_contenu = cleaned_data.get("type_contenu")
        fichier = cleaned_data.get("fichier")
        contenu_texte = cleaned_data.get("contenu_texte")

        # le champ requis dépend du type choisi : vidéo/pdf ont besoin d'un fichier, texte a besoin de contenu_texte
        if type_contenu in (Lecon.TypeContenu.VIDEO, Lecon.TypeContenu.PDF) and not fichier:
            self.add_error(
                "fichier",
                "Un fichier est requis pour une leçon de type vidéo ou PDF.",
            )
        elif type_contenu == Lecon.TypeContenu.VIDEO and fichier:
            # vérifie l'extension pour éviter qu'un formateur dépose un mauvais format de fichier
            if not fichier.name.lower().endswith((".mp4", ".mov", ".webm")):
                self.add_error("fichier", "La vidéo doit être au format .mp4, .mov ou .webm.")
        elif type_contenu == Lecon.TypeContenu.PDF and fichier:
            if not fichier.name.lower().endswith(".pdf"):
                self.add_error("fichier", "Le fichier doit être au format .pdf.")
        elif type_contenu == Lecon.TypeContenu.TEXTE and not contenu_texte:
            self.add_error("contenu_texte", "Le contenu texte est requis pour une leçon de type texte.")

        return cleaned_data


class AvisForm(forms.ModelForm):
    class Meta:
        model = Avis
        fields = ["note", "commentaire"]  # etudiant/cours assignés dans la vue, jamais choisis par l'étudiant
        widgets = {
            "note": forms.RadioSelect(
                choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)]
            ),
            "commentaire": forms.Textarea(attrs={"rows": 3}),
        }
