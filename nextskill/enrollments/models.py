"""
App: enrollments
Gère l'inscription d'un étudiant à un cours, et le suivi
de sa progression leçon par leçon.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models


class Inscription(models.Model):
    class Statut(models.TextChoices):
        EN_COURS = "en_cours", "En cours"
        TERMINE = "termine", "Terminé"

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inscriptions",
        limit_choices_to={"role": "etudiant"},
    )
    cours = models.ForeignKey(
        "courses.Cours",
        on_delete=models.CASCADE,
        related_name="inscriptions",
    )
    date_inscription = models.DateTimeField(auto_now_add=True)
    progression_pourcentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_COURS)

    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        unique_together = ("etudiant", "cours")  # une seule inscription par cours
        ordering = ["-date_inscription"]

    def __str__(self):
        return f"{self.etudiant} → {self.cours} ({self.progression_pourcentage}%)"

    def recalculer_progression(self):
        """
        Recalcule le pourcentage de progression à partir des leçons
        marquées 'terminé' pour cet étudiant sur ce cours.
        À appeler chaque fois qu'une ProgressionLecon change de statut.
        """
        total_lecons = sum(m.lecons.count() for m in self.cours.modules.all())
        if total_lecons == 0:
            self.progression_pourcentage = Decimal("0.00")
        else:
            lecons_terminees = ProgressionLecon.objects.filter(
                etudiant=self.etudiant,
                lecon__module__cours=self.cours,
                statut=ProgressionLecon.Statut.TERMINE,
            ).count()
            pourcentage = (Decimal(lecons_terminees) / Decimal(total_lecons)) * Decimal(100)
            self.progression_pourcentage = pourcentage.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        self.statut = (
            self.Statut.TERMINE
            if self.progression_pourcentage >= Decimal("100.00")
            else self.Statut.EN_COURS
        )
        self.save(update_fields=["progression_pourcentage", "statut"])


class ProgressionLecon(models.Model):
    class Statut(models.TextChoices):
        NON_COMMENCE = "non_commence", "Non commencé"
        EN_COURS = "en_cours", "En cours"
        TERMINE = "termine", "Terminé"

    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progressions_lecons",
        limit_choices_to={"role": "etudiant"},
    )
    lecon = models.ForeignKey(
        "courses.Lecon",
        on_delete=models.CASCADE,
        related_name="progressions",
    )
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.NON_COMMENCE
    )
    date_completion = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Progression de leçon"
        verbose_name_plural = "Progressions de leçons"
        unique_together = ("etudiant", "lecon")

    def __str__(self):
        return f"{self.etudiant} — {self.lecon} : {self.get_statut_display()}"

    def marquer_terminee(self):
        """Marque la leçon comme terminée et met à jour l'inscription associée."""
        from django.utils import timezone

        self.statut = self.Statut.TERMINE
        self.date_completion = timezone.now()
        self.save(update_fields=["statut", "date_completion"])

        inscription = Inscription.objects.filter(
            etudiant=self.etudiant, cours=self.lecon.module.cours
        ).first()
        if inscription:
            inscription.recalculer_progression()