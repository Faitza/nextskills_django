"""
App: accounts
Contient le modèle Utilisateur personnalisé, base de l'authentification
et de la gestion des rôles pour NextSkill.
"""
from django.conf import settings  # pour référencer AUTH_USER_MODEL sans import direct
from django.contrib.auth.models import AbstractUser  # classe de base fournie par Django pour un utilisateur personnalisé
from django.db import models  # boîte à outils des champs et modèles Django


class Utilisateur(AbstractUser):
    """
    Étend AbstractUser (fourni par Django) pour ajouter un système de rôles.
    On garde username/email/password/first_name/last_name hérités,
    et on y ajoute ce qui est spécifique à NextSkill.

    IMPORTANT : ce modèle doit être déclaré dans settings.py via
    AUTH_USER_MODEL = "accounts.Utilisateur" AVANT la première migration.
    """

    class Role(models.TextChoices):  # énumération des rôles possibles (valeur stockée, libellé affiché)
        ETUDIANT = "etudiant", "Étudiant"  # rôle par défaut à l'inscription
        FORMATEUR = "formateur", "Formateur"  # crée et gère des cours
        ADMIN = "admin", "Administrateur"  # valide les cours et supervise la plateforme

    role = models.CharField(
        max_length=20,  # assez long pour contenir la plus longue valeur ("formateur")
        choices=Role.choices,  # limite les valeurs possibles aux 3 rôles définis ci-dessus
        default=Role.ETUDIANT,  # tout nouvel utilisateur est étudiant sauf indication contraire
        help_text="Détermine les permissions et l'interface affichée à l'utilisateur.",
    )
    photo_profil = models.ImageField(
        upload_to="profils/",  # sous-dossier de MEDIA_ROOT où sont stockées les photos
        blank=True,  # facultatif dans les formulaires
        null=True,  # peut être vide en base de données
    )
    bio = models.TextField(
        blank=True,  # facultatif : tous les utilisateurs n'ont pas besoin d'une bio
        help_text="Utilisé principalement pour la page publique d'un formateur.",
    )
    specialite = models.CharField(
        max_length=150,
        blank=True,  # requis uniquement pour un formateur (validé côté formulaire, pas ici)
        help_text="Domaine d'expertise du formateur (ex: Développement web, Data Science).",
    )
    date_inscription = models.DateTimeField(auto_now_add=True)  # rempli automatiquement à la création, jamais modifié ensuite

    class Meta:
        verbose_name = "Utilisateur"  # nom singulier affiché dans l'admin Django
        verbose_name_plural = "Utilisateurs"  # nom pluriel affiché dans l'admin Django
        ordering = ["-date_inscription"]  # les plus récents inscrits apparaissent en premier

    def __str__(self):
        # affichage lisible dans l'admin et les logs : "Nom Complet (Rôle)" ou "username (Rôle)" si pas de nom
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # --- Raccourcis pratiques utilisés dans les vues et templates ---
    @property
    def est_etudiant(self):
        # "and not self.is_staff" est essentiel : createsuperuser ne renseigne jamais le
        # champ role (qui reste "etudiant" par défaut), donc sans cette exclusion un compte
        # admin serait traité comme un étudiant (pourrait acheter des cours, etc.).
        return self.role == self.Role.ETUDIANT and not self.is_staff

    @property
    def est_formateur(self):
        return self.role == self.Role.FORMATEUR and not self.is_staff  # même raison que est_etudiant ci-dessus

    @property
    def est_admin_plateforme(self):
        # note : ne remplace pas is_staff, qui reste la vraie porte d'accès au dashboard admin
        return self.role == self.Role.ADMIN


class CentreInteret(models.Model):
    """
    Lie un étudiant à une Categorie de `courses` pour laquelle il se
    déclare intéressé, choisi(e) au moment de l'inscription.

    Référence "courses.Categorie" en chaîne (et non par import direct)
    pour éviter tout risque d'import circulaire avec l'app courses.
    """

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # référence indirecte au modèle Utilisateur (bonne pratique Django)
        on_delete=models.CASCADE,  # si l'étudiant est supprimé, ses centres d'intérêt le sont aussi
        related_name="centres_interet",  # permet d'écrire utilisateur.centres_interet.all()
        limit_choices_to={"role": "etudiant"},  # limite le champ dans l'admin aux comptes étudiants
    )
    categorie = models.ForeignKey(
        "courses.Categorie",  # référence en chaîne pour éviter l'import circulaire accounts <-> courses
        on_delete=models.CASCADE,  # si la catégorie est supprimée, l'intérêt associé disparaît aussi
        related_name="centres_interet",  # permet d'écrire categorie.centres_interet.all()
    )

    class Meta:
        verbose_name = "Centre d'intérêt"
        verbose_name_plural = "Centres d'intérêt"
        unique_together = ("etudiant", "categorie")  # un étudiant ne peut déclarer deux fois le même intérêt

    def __str__(self):
        return f"{self.etudiant} — {self.categorie}"
