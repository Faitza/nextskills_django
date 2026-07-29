"""
App: orders
Gère le panier d'achat et le paiement (fictif) des cours par un étudiant.
Les deux flux — panier ET achat direct — coexistent : Paiement référence
directement les cours payés (M2M), pas le panier entier. Ça évite qu'un
achat direct sur un cours vide accidentellement le reste du panier.
"""
import uuid  # génère une référence de transaction fictive mais unique
from decimal import Decimal  # pour représenter les montants avec précision (évite les erreurs d'arrondi des float)

from django.conf import settings  # pour référencer AUTH_USER_MODEL sans import direct
from django.db import models


class Panier(models.Model):
    """Panier d'achat d'un étudiant. Un seul panier actif par étudiant."""

    etudiant = models.OneToOneField(  # un seul panier possible par étudiant (pas ForeignKey)
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # si l'étudiant est supprimé, son panier l'est aussi
        related_name="panier",  # permet d'écrire utilisateur.panier
        limit_choices_to={"role": "etudiant"},  # limite le champ dans l'admin aux comptes étudiant
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"

    def __str__(self):
        return f"Panier de {self.etudiant}"

    @property
    def montant_total(self):
        # additionne le prix de chaque cours présent dans les lignes du panier
        return sum(
            (ligne.cours.prix for ligne in self.lignes.select_related("cours")),  # select_related évite une requête par ligne
            Decimal("0.00"),  # valeur de départ, nécessaire pour que sum() reste un Decimal et non un int si le panier est vide
        )

    def vider(self):
        self.lignes.all().delete()  # supprime toutes les lignes de ce panier (appelé après un paiement réussi)


class LignePanier(models.Model):
    """Un cours ajouté au panier d'un étudiant."""

    panier = models.ForeignKey(
        Panier,
        on_delete=models.CASCADE,  # si le panier est supprimé, ses lignes le sont aussi
        related_name="lignes",  # permet d'écrire panier.lignes.all()
    )
    cours = models.ForeignKey(
        "courses.Cours",  # référence en chaîne pour éviter l'import circulaire orders <-> courses
        on_delete=models.CASCADE,  # si le cours est supprimé, les lignes de panier associées le sont aussi
        related_name="lignes_panier",  # permet d'écrire cours.lignes_panier.all()
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ligne de panier"
        verbose_name_plural = "Lignes de panier"
        unique_together = ("panier", "cours")  # un même cours ne peut apparaître deux fois dans le même panier
        ordering = ["date_ajout"]  # ordre d'ajout, du plus ancien au plus récent

    def __str__(self):
        return f"{self.panier} — {self.cours}"


class Paiement(models.Model):
    """
    Paiement fictif d'une sélection de cours (panier entier ou achat direct
    d'un seul cours). Aucune vraie transaction : la validation est simulée
    côté application.
    """

    class Methode(models.TextChoices):  # les 3 modes de paiement fictifs proposés à l'étudiant
        MONCASH = "moncash", "MonCash"
        CARTE = "carte", "Carte bancaire"
        VIREMENT = "virement", "Virement"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"  # valeur par défaut, jamais montrée en pratique car valider() s'exécute juste après création
        REUSSI = "reussi", "Réussi"
        ECHOUE = "echoue", "Échoué"  # non utilisé actuellement (paiement fictif toujours réussi), réservé pour une évolution future

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # si l'étudiant est supprimé, ses paiements le sont aussi
        related_name="paiements",  # permet d'écrire utilisateur.paiements.all()
        limit_choices_to={"role": "etudiant"},  # limite le champ dans l'admin aux comptes étudiant
    )
    cours = models.ManyToManyField(  # plusieurs cours possibles (checkout panier) ou un seul (achat direct)
        "courses.Cours",
        related_name="paiements",  # permet d'écrire cours.paiements.all()
        help_text="Cours couverts par ce paiement (un seul en achat direct, plusieurs en checkout panier).",
    )
    montant = models.DecimalField(max_digits=8, decimal_places=2)  # total figé au moment du paiement (indépendant du prix futur des cours)
    methode = models.CharField(max_length=20, choices=Methode.choices)
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE
    )
    reference_transaction = models.CharField(max_length=50, unique=True, blank=True)  # généré automatiquement dans save(), jamais saisi à la main
    date_paiement = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-date_paiement"]  # les plus récents en premier

    def __str__(self):
        return f"{self.etudiant} — {self.montant} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.reference_transaction:  # ne régénère jamais une référence déjà existante
            self.reference_transaction = uuid.uuid4().hex[:20].upper()  # identifiant fictif, unique et lisible
        super().save(*args, **kwargs)  # enregistrement réel en base, délégué au parent

    def valider(self):
        """
        Simule la réussite du paiement : inscrit l'étudiant à chaque cours
        couvert par ce paiement, et retire uniquement ces cours-là du panier
        (s'ils s'y trouvaient) — un achat direct ne touche pas le reste du
        panier. Aucune vraie passerelle bancaire n'est appelée (paiement
        fictif, voir CLAUDE.md).
        """
        from enrollments.models import Inscription  # import local pour éviter un import circulaire orders <-> enrollments au chargement du module

        self.statut = self.Statut.REUSSI
        self.save(update_fields=["statut"])  # ne réécrit que ce champ, plus efficace qu'un save() complet

        cours_payes = list(self.cours.all())  # matérialise la liste une fois, réutilisée deux fois ci-dessous
        for cours in cours_payes:
            # get_or_create évite une erreur si l'étudiant était déjà inscrit (ex: cours gratuit ajouté deux fois)
            Inscription.objects.get_or_create(etudiant=self.etudiant, cours=cours)

        # ne supprime que les lignes correspondant aux cours réellement payés ici,
        # jamais tout le panier : c'est ce qui permet à l'achat direct de coexister avec le panier
        LignePanier.objects.filter(
            panier__etudiant=self.etudiant, cours__in=cours_payes
        ).delete()
