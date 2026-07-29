"""
App: enrollments
Gère l'inscription d'un étudiant à un cours, et le suivi
de sa progression leçon par leçon.
"""
from decimal import Decimal, ROUND_HALF_UP  # calcul précis du pourcentage, arrondi "classique" au lieu de l'arrondi bancaire par défaut

from django.conf import settings  # pour référencer AUTH_USER_MODEL sans import direct
from django.db import models


class Inscription(models.Model):
    class Statut(models.TextChoices):  # évolue automatiquement selon la progression, jamais choisi à la main
        EN_COURS = "en_cours", "En cours"
        TERMINE = "termine", "Terminé"

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # si l'étudiant est supprimé, ses inscriptions le sont aussi
        related_name="inscriptions",  # permet d'écrire utilisateur.inscriptions.all()
        limit_choices_to={"role": "etudiant"},  # limite le champ dans l'admin aux comptes étudiant
    )
    cours = models.ForeignKey(
        "courses.Cours",  # référence en chaîne pour éviter l'import circulaire enrollments <-> courses
        on_delete=models.CASCADE,  # si le cours est supprimé, les inscriptions associées le sont aussi
        related_name="inscriptions",  # permet d'écrire cours.inscriptions.all()
    )
    date_inscription = models.DateTimeField(auto_now_add=True)
    progression_pourcentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")  # ex: 100.00, jamais modifié à la main, voir recalculer_progression()
    )
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_COURS)

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        unique_together = ("etudiant", "cours")  # une seule inscription par cours
        ordering = ["-date_inscription"]  # les plus récentes en premier

    def __str__(self):
        return f"{self.etudiant} → {self.cours} ({self.progression_pourcentage}%)"

    def recalculer_progression(self):
        """
        Recalcule le pourcentage de progression à partir des leçons
        marquées 'terminé' pour cet étudiant sur ce cours.
        À appeler chaque fois qu'une ProgressionLecon change de statut.
        """
        total_lecons = sum(m.lecons.count() for m in self.cours.modules.all())  # nombre total de leçons, tous modules confondus
        if total_lecons == 0:
            self.progression_pourcentage = Decimal("0.00")  # évite une division par zéro si le cours n'a encore aucune leçon
        else:
            lecons_terminees = ProgressionLecon.objects.filter(
                etudiant=self.etudiant,
                lecon__module__cours=self.cours,  # ne compte que les leçons de CE cours (un étudiant peut suivre plusieurs cours)
                statut=ProgressionLecon.Statut.TERMINE,
            ).count()
            pourcentage = (Decimal(lecons_terminees) / Decimal(total_lecons)) * Decimal(100)
            self.progression_pourcentage = pourcentage.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP  # arrondit à 2 décimales, ex: 33.333... -> 33.33
            )

        self.statut = (
            self.Statut.TERMINE
            if self.progression_pourcentage >= Decimal("100.00")  # 100% de leçons terminées = cours terminé
            else self.Statut.EN_COURS
        )
        self.save(update_fields=["progression_pourcentage", "statut"])  # ne réécrit que ces deux champs, plus efficace qu'un save() complet


class ProgressionLecon(models.Model):
    class Statut(models.TextChoices):
        NON_COMMENCE = "non_commence", "Non commencé"  # valeur par défaut à la création (get_or_create dans courses/views.py)
        EN_COURS = "en_cours", "En cours"  # non utilisé actuellement (pas de suivi partiel intra-leçon), réservé pour une évolution future
        TERMINE = "termine", "Terminé"

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # si l'étudiant est supprimé, ses progressions le sont aussi
        related_name="progressions_lecons",  # permet d'écrire utilisateur.progressions_lecons.all()
        limit_choices_to={"role": "etudiant"},  # limite le champ dans l'admin aux comptes étudiant
    )
    lecon = models.ForeignKey(
        "courses.Lecon",  # référence en chaîne pour éviter l'import circulaire enrollments <-> courses
        on_delete=models.CASCADE,  # si la leçon est supprimée, les progressions associées le sont aussi
        related_name="progressions",  # permet d'écrire lecon.progressions.all()
    )
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.NON_COMMENCE
    )
    date_completion = models.DateTimeField(blank=True, null=True)  # rempli uniquement quand statut passe à TERMINE

    class Meta:
        verbose_name = "Progression de leçon"
        verbose_name_plural = "Progressions de leçons"
        unique_together = ("etudiant", "lecon")  # un seul enregistrement de progression par étudiant et par leçon

    def __str__(self):
        return f"{self.etudiant} — {self.lecon} : {self.get_statut_display()}"

    def marquer_terminee(self):
        """Marque la leçon comme terminée et met à jour l'inscription associée."""
        from django.utils import timezone  # import local pour éviter un import inutile si cette méthode n'est jamais appelée

        self.statut = self.Statut.TERMINE
        self.date_completion = timezone.now()  # horodatage du moment où la leçon est terminée
        self.save(update_fields=["statut", "date_completion"])

        # répercute immédiatement le changement sur le pourcentage global du cours
        inscription = Inscription.objects.filter(
            etudiant=self.etudiant, cours=self.lecon.module.cours
        ).first()
        if inscription:  # garde-fou : normalement toujours vrai puisque lire_lecon() exige déjà une inscription
            inscription.recalculer_progression()
