from django.db import models

# Create your models here.
"""
App: accounts
Contient le modèle Utilisateur personnalisé, base de l'authentification
et de la gestion des rôles pour NextSkill.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class Utilisateur(AbstractUser):
    """
    Étend AbstractUser (fourni par Django) pour ajouter un système de rôles.
    On garde username/email/password/first_name/last_name hérités,
    et on y ajoute ce qui est spécifique à NextSkill.

    IMPORTANT : ce modèle doit être déclaré dans settings.py via
    AUTH_USER_MODEL = "accounts.Utilisateur" AVANT la première migration.
    """

    class Role(models.TextChoices):
        ETUDIANT = "etudiant", "Étudiant"
        FORMATEUR = "formateur", "Formateur"
        ADMIN = "admin", "Administrateur"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ETUDIANT,
        help_text="Détermine les permissions et l'interface affichée à l'utilisateur.",
    )
    photo_profil = models.ImageField(
        upload_to="profils/",
        blank=True,
        null=True,
    )
    bio = models.TextField(
        blank=True,
        help_text="Utilisé principalement pour la page publique d'un formateur.",
    )
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["-date_inscription"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # --- Raccourcis pratiques utilisés dans les vues et templates ---
    @property
    def est_etudiant(self):
        return self.role == self.Role.ETUDIANT

    @property
    def est_formateur(self):
        return self.role == self.Role.FORMATEUR

    @property
    def est_admin_plateforme(self):
        return self.role == self.Role.ADMIN