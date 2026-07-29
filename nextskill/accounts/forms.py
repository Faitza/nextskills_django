"""Formulaires d'authentification : connexion et inscription (étudiant/formateur)."""
from django import forms  # briques de base des formulaires Django
from django.contrib.auth import get_user_model  # récupère le modèle utilisateur actif du projet (Utilisateur)

from courses.models import Categorie  # nécessaire pour proposer les centres d'intérêt à l'inscription

from .models import CentreInteret  # modèle de liaison étudiant <-> catégorie

Utilisateur = get_user_model()  # alias pratique, évite d'importer accounts.models.Utilisateur directement


class InscriptionForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=[
            (Utilisateur.Role.ETUDIANT, "Étudiant"),  # seuls étudiant/formateur sont proposés à l'inscription
            (Utilisateur.Role.FORMATEUR, "Formateur"),  # l'admin est créé uniquement via createsuperuser
        ],
        widget=forms.RadioSelect,  # affiché comme deux boutons "onglet" dans le template, pas une liste déroulante
        initial=Utilisateur.Role.ETUDIANT,  # étudiant sélectionné par défaut à l'ouverture du formulaire
    )
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")  # champ hors Meta.fields car il doit être hashé manuellement dans save()
    centres_interet = forms.ModelMultipleChoiceField(
        queryset=Categorie.objects.all(),  # liste toutes les catégories existantes comme choix possibles
        required=False,  # un étudiant peut ne cocher aucun centre d'intérêt
        widget=forms.CheckboxSelectMultiple,  # affiche une case à cocher par catégorie
        label="Quels sujets t'intéressent le plus ?",
    )
    specialite = forms.CharField(max_length=150, required=False, label="Ta spécialité")  # requis seulement si role=formateur, vérifié dans clean()
    bio = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,  # facultatif même pour un formateur
        label="Parle-nous de toi",
    )

    class Meta:
        model = Utilisateur  # ce formulaire crée/modifie une instance d'Utilisateur
        fields = ["username", "email", "password", "role"]  # champs directement liés au modèle (le reste est géré manuellement)

    def clean(self):
        cleaned_data = super().clean()  # récupère les données déjà validées champ par champ
        # un formateur doit obligatoirement renseigner sa spécialité (règle métier, pas une contrainte de modèle)
        if cleaned_data.get("role") == Utilisateur.Role.FORMATEUR and not cleaned_data.get(
            "specialite"
        ):
            self.add_error("specialite", "La spécialité est requise pour un formateur.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)  # crée l'objet en mémoire sans encore l'enregistrer en base
        user.set_password(self.cleaned_data["password"])  # hash le mot de passe (jamais stocké en clair)
        user.role = self.cleaned_data["role"]  # applique le rôle choisi (pas dans Meta.fields par défaut de ModelForm car CharField custom)
        if user.role == Utilisateur.Role.FORMATEUR:
            # spécialité/bio ne concernent que les formateurs ; on les ignore si étudiant
            user.specialite = self.cleaned_data.get("specialite", "")
            user.bio = self.cleaned_data.get("bio", "")
        if commit:
            user.save()  # écrit réellement l'utilisateur en base maintenant
            if user.role == Utilisateur.Role.ETUDIANT:
                # crée un CentreInteret pour chaque catégorie cochée par l'étudiant
                for categorie in self.cleaned_data.get("centres_interet", []):
                    CentreInteret.objects.get_or_create(etudiant=user, categorie=categorie)
        return user
