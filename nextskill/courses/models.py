"""
App: courses
Contient toute la hiérarchie de contenu pédagogique :
Categorie -> Cours -> Module -> Lecon
"""
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Cours(models.Model):
    class Niveau(models.TextChoices):
        DEBUTANT = "debutant", "Débutant"
        INTERMEDIAIRE = "intermediaire", "Intermédiaire"
        AVANCE = "avance", "Avancé"

    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EN_ATTENTE = "en_attente", "En attente de validation"
        PUBLIE = "publie", "Publié"
        REJETE = "rejete", "Rejeté"

    titre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    niveau = models.CharField(max_length=20, choices=Niveau.choices, default=Niveau.DEBUTANT)
    langue = models.CharField(max_length=50, default="Français")
    image_couverture = models.ImageField(upload_to="cours/couvertures/", blank=True, null=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.BROUILLON)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)

    formateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cours_crees",
        limit_choices_to={"role": "formateur"},
    )
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name="cours",
    )

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ["-date_creation"]

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        # Génère automatiquement le slug à partir du titre (une seule fois)
        if not self.slug:
            self.slug = slugify(self.titre)
        super().save(*args, **kwargs)

    @property
    def nombre_inscrits(self):
        return self.inscriptions.count()

    @property
    def nombre_modules(self):
        return self.modules.count()


class Module(models.Model):
    titre = models.CharField(max_length=200)
    ordre = models.PositiveIntegerField(
        default=0,
        help_text="Définit la position du module dans le cours (0, 1, 2...).",
    )
    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,
        related_name="modules",
    )

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ["cours", "ordre"]
        unique_together = ("cours", "ordre")

    def __str__(self):
        return f"{self.cours.titre} — Module {self.ordre}: {self.titre}"


class Lecon(models.Model):
    class TypeContenu(models.TextChoices):
        VIDEO = "video", "Vidéo"
        PDF = "pdf", "PDF"
        TEXTE = "texte", "Texte"

    titre = models.CharField(max_length=200)
    type_contenu = models.CharField(max_length=10, choices=TypeContenu.choices)
    fichier = models.FileField(
        upload_to="lecons/fichiers/",
        blank=True,
        null=True,
        help_text="Vidéo (mp4) ou PDF selon le type_contenu.",
    )
    contenu_texte = models.TextField(
        blank=True,
        help_text="Utilisé uniquement si type_contenu = texte.",
    )
    duree_minutes = models.PositiveIntegerField(blank=True, null=True)
    ordre = models.PositiveIntegerField(default=0)
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lecons",
    )

    class Meta:
        verbose_name = "Leçon"
        verbose_name_plural = "Leçons"
        ordering = ["module", "ordre"]
        unique_together = ("module", "ordre")

    def __str__(self):
        return f"{self.module.titre} — {self.titre}"