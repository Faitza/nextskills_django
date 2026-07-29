"""
App: enrollments
Tableau de bord étudiant : liste des cours suivis et leur progression,
et génération du certificat de complétion (PDF) une fois un cours terminé.
"""
from decimal import Decimal

from django.contrib import messages  # messages flash affichés en haut de page après une action
from django.contrib.auth.decorators import login_required  # protège la vue : redirige vers /connexion/ si anonyme
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import Inscription


@login_required
def mes_cours(request):
    if not request.user.est_etudiant:  # un formateur/admin n'a pas de page "Mes cours"
        messages.error(request, "Cette page est réservée aux étudiants.")
        return redirect("pages:accueil")

    inscriptions = Inscription.objects.filter(etudiant=request.user).select_related(
        "cours", "cours__formateur"  # évite une requête SQL par inscription pour afficher le cours et son formateur
    )
    return render(request, "enrollments/mes_cours.html", {"inscriptions": inscriptions})


def _inscription_terminee_ou_erreur(request, inscription_id):
    """Récupère l'inscription si elle appartient à l'étudiant connecté ET que le
    cours est effectivement terminé à 100 % — impossible de deviner l'URL d'un
    autre étudiant ou d'obtenir un certificat non mérité.

    Retourne (inscription, None) si tout est en ordre, ou (None, redirect) sinon
    — réutilisé par l'aperçu HTML et le téléchargement PDF du certificat.
    """
    inscription = get_object_or_404(Inscription, id=inscription_id, etudiant=request.user)

    if inscription.statut != Inscription.Statut.TERMINE or inscription.progression_pourcentage < Decimal("100.00"):
        messages.error(request, "Ce cours doit être terminé à 100 % pour obtenir le certificat.")
        return None, redirect("enrollments:mes_cours")

    return inscription, None


@login_required
def apercu_certificat(request, inscription_id):
    """Page d'aperçu : affiche l'image du certificat (voir image_certificat) avant téléchargement du PDF."""
    inscription, redirection = _inscription_terminee_ou_erreur(request, inscription_id)
    if redirection:
        return redirection
    return render(request, "enrollments/apercu_certificat.html", {"inscription": inscription})


@login_required
def image_certificat(request, inscription_id):
    """Convertit la première page du PDF réel en image PNG, pour un aperçu
    strictement identique à ce que l'étudiant obtiendra en téléchargeant."""
    inscription, redirection = _inscription_terminee_ou_erreur(request, inscription_id)
    if redirection:
        return redirection

    import fitz  # PyMuPDF — rend une page PDF en image sans dépendance système externe (contrairement à poppler)

    pdf_bytes = generer_pdf_certificat(inscription)
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = document[0]
    # zoom 2x : le PDF est en A4 paysage, un rendu 1x serait trop basse résolution pour un écran
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    png_bytes = pixmap.tobytes("png")
    document.close()

    return HttpResponse(png_bytes, content_type="image/png")


@login_required
def certificat(request, inscription_id):
    """Génère et renvoie le certificat de complétion en PDF (téléchargement)."""
    inscription, redirection = _inscription_terminee_ou_erreur(request, inscription_id)
    if redirection:
        return redirection

    pdf_bytes = generer_pdf_certificat(inscription)

    nom_fichier = f"certificat-{inscription.cours.slug}.pdf"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
    return response


def generer_pdf_certificat(inscription):
    """Construit le PDF du certificat avec reportlab et retourne les octets du fichier.

    Fonction séparée de la vue pour rester testable indépendamment de request/response.
    """
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas

    NAVY = colors.HexColor("#152B54")
    ORANGE = colors.HexColor("#F2662D")
    INK_SOFT = colors.HexColor("#5A5F76")

    buffer = BytesIO()
    largeur, hauteur = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Fond et bordures décoratives
    c.setFillColor(colors.white)
    c.rect(0, 0, largeur, hauteur, fill=1, stroke=0)
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.rect(1.2 * cm, 1.2 * cm, largeur - 2.4 * cm, hauteur - 2.4 * cm)
    c.setStrokeColor(ORANGE)
    c.setLineWidth(1)
    c.rect(1.5 * cm, 1.5 * cm, largeur - 3 * cm, hauteur - 3 * cm)

    # En-tête
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(largeur / 2, hauteur - 4 * cm, "NEXTSKILL")
    c.setFont("Helvetica-Oblique", 12)
    c.setFillColor(INK_SOFT)
    c.drawCentredString(largeur / 2, hauteur - 4.7 * cm, "Plateforme d'apprentissage en ligne")

    # Titre du certificat
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largeur / 2, hauteur - 7 * cm, "CERTIFICAT DE COMPLÉTION")

    # Nom de l'étudiant
    nom_etudiant = inscription.etudiant.get_full_name() or inscription.etudiant.username
    c.setFillColor(colors.HexColor("#161A2B"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(largeur / 2, hauteur - 9 * cm, "Ce certificat est décerné à")
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(NAVY)
    c.drawCentredString(largeur / 2, hauteur - 10.2 * cm, nom_etudiant)

    # Nom du cours
    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#161A2B"))
    c.drawCentredString(largeur / 2, hauteur - 12 * cm, "pour avoir complété avec succès le cours")
    c.setFont("Helvetica-Bold", 17)
    c.setFillColor(ORANGE)
    c.drawCentredString(largeur / 2, hauteur - 13.1 * cm, inscription.cours.titre)

    # Formateur et date
    c.setFont("Helvetica", 11)
    c.setFillColor(INK_SOFT)
    nom_formateur = inscription.cours.formateur.get_full_name() or inscription.cours.formateur.username
    c.drawCentredString(
        largeur / 2, hauteur - 14.3 * cm,
        f"Formateur : {nom_formateur}"
    )
    date_str = inscription.date_inscription.strftime("%d/%m/%Y")
    c.drawCentredString(largeur / 2, 2.8 * cm, f"Délivré le {date_str} — NextSkill, ITAC")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()