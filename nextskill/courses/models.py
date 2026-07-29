"""
App: courses
Contient toute la hiérarchie de contenu pédagogique :
Categorie -> Cours -> Module -> Lecon
"""
from decimal import Decimal  # pour représenter le prix avec précision (évite les erreurs d'arrondi des float)

from django.conf import settings  # pour référencer AUTH_USER_MODEL sans import direct
from django.core.exceptions import ValidationError  # levée quand une note d'avis est hors limites
from django.core.validators import MaxValueValidator, MinValueValidator  # bornent la note d'un Avis entre 1 et 5
from django.db import models
from django.utils.text import slugify  # transforme un titre en slug utilisable dans une URL


class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)  # unique pour éviter les doublons de catégorie
    description = models.TextField(blank=True)  # facultative

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["nom"]  # tri alphabétique par défaut

    def __str__(self):
        return self.nom


class Cours(models.Model):
    class Niveau(models.TextChoices):  # niveau de difficulté affiché sur la fiche cours
        DEBUTANT = "debutant", "Débutant"
        INTERMEDIAIRE = "intermediaire", "Intermédiaire"
        AVANCE = "avance", "Avancé"

    class Statut(models.TextChoices):  # cycle de vie d'un cours, du brouillon à la publication
        BROUILLON = "brouillon", "Brouillon"
        EN_ATTENTE = "en_attente", "En attente de validation"  # soumis par le formateur, attend l'admin
        PUBLIE = "publie", "Publié"  # visible dans le catalogue public
        REJETE = "rejete", "Rejeté"  # refusé par l'administration

    titre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)  # généré automatiquement dans save(), jamais saisi à la main
    description = models.TextField()  # obligatoire, contrairement à celle de Categorie
    niveau = models.CharField(max_length=20, choices=Niveau.choices, default=Niveau.DEBUTANT)
    langue = models.CharField(max_length=50, default="Français")
    prix = models.DecimalField(
        max_digits=8,  # jusqu'à 999999.99
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Prix du cours en gourdes. 0 = cours gratuit.",
    )
    image_couverture = models.ImageField(upload_to="cours/couvertures/", blank=True, null=True)  # affichée dans le catalogue et le détail
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.BROUILLON)
    date_creation = models.DateTimeField(auto_now_add=True)  # figée à la création
    date_maj = models.DateTimeField(auto_now=True)  # mise à jour à chaque save()

    formateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # si le formateur est supprimé, ses cours le sont aussi
        related_name="cours_crees",  # permet d'écrire utilisateur.cours_crees.all()
        limit_choices_to={"role": "formateur"},  # limite le champ dans l'admin aux comptes formateur
    )
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,  # empêche de supprimer une catégorie tant qu'un cours y est rattaché
        related_name="cours",
    )

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"  # identique au singulier ("des cours"), sinon Django afficherait "Courss"
        ordering = ["-date_creation"]  # les plus récents en premier

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        # Génère automatiquement le slug à partir du titre (une seule fois)
        if not self.slug:  # ne régénère jamais un slug déjà existant, pour ne pas casser les URLs déjà partagées
            self.slug = slugify(self.titre)
        super().save(*args, **kwargs)  # enregistrement réel en base, délégué au parent

    @property
    def nombre_inscrits(self):
        return self.inscriptions.count()  # related_name défini sur Inscription.cours (app enrollments)

    @property
    def nombre_modules(self):
        return self.modules.count()  # related_name défini sur Module.cours ci-dessous


class Module(models.Model):
    titre = models.CharField(max_length=200)
    ordre = models.PositiveIntegerField(
        default=0,
        help_text="Définit la position du module dans le cours (0, 1, 2...).",
    )
    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,  # si le cours est supprimé, ses modules le sont aussi
        related_name="modules",
    )

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ["cours", "ordre"]  # affichage dans l'ordre pédagogique voulu par le formateur
        unique_together = ("cours", "ordre")  # deux modules d'un même cours ne peuvent pas partager le même ordre

    def __str__(self):
        return f"{self.cours.titre} — Module {self.ordre}: {self.titre}"


class Lecon(models.Model):
    class TypeContenu(models.TextChoices):  # détermine quel champ contient le vrai contenu (fichier ou texte)
        VIDEO = "video", "Vidéo"
        PDF = "pdf", "PDF"
        TEXTE = "texte", "Texte"

    titre = models.CharField(max_length=200)
    type_contenu = models.CharField(max_length=10, choices=TypeContenu.choices)
    fichier = models.FileField(
        upload_to="lecons/fichiers/",
        blank=True,  # vide si type_contenu = texte
        null=True,
        help_text="Vidéo (mp4) ou PDF selon le type_contenu.",
    )
    contenu_texte = models.TextField(
        blank=True,  # vide si type_contenu = video/pdf
        help_text="Utilisé uniquement si type_contenu = texte.",
    )
    duree_minutes = models.PositiveIntegerField(blank=True, null=True)  # facultatif, informatif uniquement
    ordre = models.PositiveIntegerField(default=0)
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,  # si le module est supprimé, ses leçons le sont aussi
        related_name="lecons",
    )

    class Meta:
        verbose_name = "Leçon"
        verbose_name_plural = "Leçons"
        ordering = ["module", "ordre"]  # affichage dans l'ordre pédagogique voulu par le formateur
        unique_together = ("module", "ordre")  # deux leçons d'un même module ne peuvent pas partager le même ordre

    def __str__(self):
        return f"{self.module.titre} — {self.titre}"


class Avis(models.Model):
    """Note (1 à 5 étoiles) et commentaire laissés par un étudiant sur un cours."""

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # si l'étudiant est supprimé, son avis l'est aussi
        related_name="avis",
        limit_choices_to={"role": "etudiant"},  # limite le champ dans l'admin aux comptes étudiant
    )
    cours = models.ForeignKey(
        Cours,
        on_delete=models.CASCADE,  # si le cours est supprimé, les avis associés le sont aussi
        related_name="avis",
    )
    note = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],  # rejette toute valeur hors de 1-5 dans les formulaires
        help_text="Note de 1 à 5 étoiles.",
    )
    commentaire = models.TextField(blank=True)  # la note seule suffit, le commentaire est optionnel
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"  # identique au singulier en français
        unique_together = ("etudiant", "cours")  # un étudiant ne peut laisser qu'un seul avis par cours
        ordering = ["-date_creation"]  # les plus récents en premier

    def __str__(self):
        return f"{self.etudiant} — {self.cours} : {self.note}/5"

    def clean(self):
        # sécurité supplémentaire au niveau modèle, en plus des validators du champ note
        if not (1 <= self.note <= 5):
            raise ValidationError("La note doit être comprise entre 1 et 5.")
