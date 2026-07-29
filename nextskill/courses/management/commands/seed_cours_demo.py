"""
Commande de seed : crée des formateurs et des cours publiés par défaut,
un (ou deux) par catégorie, pour peupler le site avec du contenu réaliste.

Usage : python manage.py seed_cours_demo
Idempotent : ne recrée pas un cours dont le titre existe déjà.
"""
from decimal import Decimal  # pour représenter les prix avec précision (évite les erreurs d'arrondi des float)
from pathlib import Path  # manipulation de chemins indépendante de l'OS, pour localiser les images/vidéos de seed

from django.contrib.auth import get_user_model  # récupère le modèle utilisateur actif du projet (Utilisateur)
from django.core.files import File  # enveloppe un fichier ouvert pour l'assigner à un FileField/ImageField
from django.core.management.base import BaseCommand  # classe de base pour créer une commande `manage.py`
from django.db import transaction  # garantit que tout réussit ou rien n'est enregistré

from courses.models import Categorie, Cours, Lecon, Module
from quizzes.models import Question, Quiz, ReponseOption

Utilisateur = get_user_model()  # alias pratique, évite d'importer accounts.models.Utilisateur directement

COVERS_DIR = Path(__file__).resolve().parent / "seed_covers"  # dossier contenant les images/vidéo fournies avec cette commande
SAMPLE_VIDEO = COVERS_DIR / "sample-lesson-video.mp4"  # vidéo d'exemple réutilisée pour toutes les leçons vidéo de démo

# Données des 5 formateurs de démonstration : chaque dict devient un compte Utilisateur (role=FORMATEUR)
FORMATEURS = [
    {
        "username": "nadege.similien",
        "first_name": "Nadège",
        "last_name": "Similien",
        "specialite": "Développement Web (Django, API REST)",
        "bio": "Développeuse Django depuis 6 ans, spécialisée en architecture MVT et API REST.",
    },
    {
        "username": "jean.prophete",
        "first_name": "Jean",
        "last_name": "Prophète",
        "specialite": "Python et Data Science",
        "bio": "Formateur passionné par l'enseignement des fondamentaux de la programmation.",
    },
    {
        "username": "farah.delva",
        "first_name": "Farah",
        "last_name": "Delva",
        "specialite": "Design UI/UX",
        "bio": "Designeuse UI/UX, spécialisée dans les outils Figma et le design system.",
    },
    {
        "username": "wilner.auguste",
        "first_name": "Wilner",
        "last_name": "Auguste",
        "specialite": "Réseaux et Bureautique",
        "bio": "Formateur en réseaux Cisco et outils bureautiques pour professionnels.",
    },
    {
        "username": "marie.toussaint",
        "first_name": "Marie",
        "last_name": "Toussaint",
        "specialite": "Langues (Anglais professionnel)",
        "bio": "Professeure d'anglais professionnel, spécialisée dans la préparation aux entretiens.",
    },
]

# Données des cours de démonstration : un (ou deux) par catégorie, chacun avec ses
# modules et leçons ; "cover" pointe vers une image dans seed_covers/, "quiz" est
# optionnel et n'est présent que sur le premier module du cours Django.
COURS_PAR_CATEGORIE = [
    {
        "categorie": "Programmation",
        "formateur": "nadege.similien",
        "titre": "Développement Web avec Django",
        "cover": "cov_django.jpg",
        "description": "Construire une plateforme complète avec l'architecture MVT, de l'authentification aux modèles de données.",
        "niveau": Cours.Niveau.INTERMEDIAIRE,
        "prix": Decimal("2500.00"),
        "modules": [
            {
                "titre": "Introduction à Django et à l'architecture MVT",
                "lecons": [
                    ("Qu'est-ce que Django ?", "video", 8),  # (titre, type_contenu, durée en minutes)
                    ("Le patron Model-View-Template", "video", 12),
                ],
                "quiz": {
                    "titre": "Fondamentaux MVT",
                    "note_passage": 60,
                    "questions": [
                        # (énoncé, [(texte_option, est_correcte), ...])
                        ("Django est un framework pour quel langage ?", [("Python", True), ("JavaScript", False)]),
                        ("Que signifie MVT ?", [("Model View Template", True), ("Multi Virtual Thread", False)]),
                    ],
                },
            },
            {
                "titre": "Modèles et bases de données",
                "lecons": [
                    ("Créer des modèles avec l'ORM", "video", 15),
                    ("Support de cours — Relations FK", "pdf", None),  # pas de durée pour un PDF
                ],
            },
        ],
    },
    {
        "categorie": "Programmation",
        "formateur": "jean.prophete",
        "titre": "Introduction à Python",
        "cover": "cov_python.jpg",
        "description": "Les bases du langage Python : variables, boucles, fonctions et structures de données.",
        "niveau": Cours.Niveau.DEBUTANT,
        "prix": Decimal("0.00"),  # cours gratuit
        "modules": [
            {
                "titre": "Premiers pas avec Python",
                "lecons": [
                    ("Installer Python et un éditeur", "video", 10),
                    ("Variables et types de données", "video", 14),
                    ("Les boucles for et while", "video", 11),
                ],
            },
        ],
    },
    {
        "categorie": "Réseaux",
        "formateur": "wilner.auguste",
        "titre": "Réseaux Cisco pour Débutants",
        "cover": "cov_reseaux2.jpg",
        "description": "Comprendre les bases des réseaux informatiques et s'initier aux équipements Cisco.",
        "niveau": Cours.Niveau.DEBUTANT,
        "prix": Decimal("1800.00"),
        "modules": [
            {
                "titre": "Fondamentaux des réseaux",
                "lecons": [
                    ("Le modèle OSI expliqué", "video", 13),
                    ("Adressage IP et sous-réseaux", "video", 18),
                ],
            },
        ],
    },
    {
        "categorie": "Design",
        "formateur": "farah.delva",
        "titre": "Design UI/UX avec Figma",
        "cover": "cov_design.jpg",
        "description": "Apprends à concevoir des interfaces claires et à créer des prototypes interactifs avec Figma.",
        "niveau": Cours.Niveau.DEBUTANT,
        "prix": Decimal("1200.00"),
        "modules": [
            {
                "titre": "Les fondamentaux du design d'interface",
                "lecons": [
                    ("Principes de base UI/UX", "video", 12),
                    ("Prise en main de Figma", "video", 16),
                ],
            },
        ],
    },
    {
        "categorie": "Langues",
        "formateur": "marie.toussaint",
        "titre": "Anglais professionnel A2",
        "cover": "cov_anglais.jpg",
        "description": "Développe ton anglais pour le monde du travail : emails, entretiens et réunions.",
        "niveau": Cours.Niveau.DEBUTANT,
        "prix": Decimal("1000.00"),
        "modules": [
            {
                "titre": "Communication professionnelle de base",
                "lecons": [
                    ("Se présenter en anglais", "video", 9),
                    ("Rédiger un email professionnel", "texte", None),  # pas de durée pour une leçon texte
                ],
            },
        ],
    },
    {
        "categorie": "Bureautique",
        "formateur": "wilner.auguste",
        "titre": "Excel pour la gestion",
        "cover": "cov_excel2.jpg",
        "description": "Maîtrise les fonctions essentielles d'Excel pour la gestion administrative et financière.",
        "niveau": Cours.Niveau.DEBUTANT,
        "prix": Decimal("900.00"),
        "modules": [
            {
                "titre": "Les bases d'Excel",
                "lecons": [
                    ("Formules et fonctions essentielles", "video", 14),
                    ("Tableaux croisés dynamiques", "video", 17),
                ],
            },
        ],
    },
    {
        "categorie": "Data / IA",
        "formateur": "jean.prophete",
        "titre": "Introduction à la Data Science",
        "cover": "cov_data.jpg",
        "description": "Découvre les bases de l'analyse de données et du machine learning avec Python.",
        "niveau": Cours.Niveau.INTERMEDIAIRE,
        "prix": Decimal("2200.00"),
        "modules": [
            {
                "titre": "Analyse de données avec Python",
                "lecons": [
                    ("Introduction à pandas", "video", 16),
                    ("Visualiser des données", "video", 13),
                ],
            },
        ],
    },
]


class Command(BaseCommand):  # nom de fichier = nom de la commande : `python manage.py seed_cours_demo`
    help = "Crée des formateurs et des cours publiés par défaut, un par catégorie, pour peupler le site."

    @transaction.atomic  # si une erreur survient en cours de route, rien n'est enregistré (tout ou rien)
    def handle(self, *args, **options):
        formateurs = {}  # dict {username: objet Utilisateur}, réutilisé plus bas pour associer chaque cours à son formateur
        for data in FORMATEURS:
            formateur, created = Utilisateur.objects.get_or_create(
                username=data["username"],  # clé de recherche/création : ne crée pas de doublon si déjà exécuté une fois
                defaults={  # valeurs utilisées uniquement si le compte n'existe pas encore
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": Utilisateur.Role.FORMATEUR,
                    "specialite": data["specialite"],
                    "bio": data["bio"],
                },
            )
            if created:
                formateur.set_password("nextskill2026")  # mot de passe fixe pour tous les comptes de démo, hashé avant sauvegarde
                formateur.save()
            formateurs[data["username"]] = formateur  # mémorisé pour la boucle des cours ci-dessous
            self.stdout.write(f"Formateur {'créé' if created else 'déjà existant'} : {formateur.username}")  # trace affichée dans le terminal

        for data in COURS_PAR_CATEGORIE:
            categorie, _ = Categorie.objects.get_or_create(nom=data["categorie"])  # crée la catégorie si elle n'existe pas encore
            formateur = formateurs[data["formateur"]]  # récupère l'objet Utilisateur créé/trouvé plus haut

            if Cours.objects.filter(titre=data["titre"]).exists():
                # rend la commande idempotente : relancer le script ne duplique pas les cours déjà créés
                self.stdout.write(f"Cours déjà existant, ignoré : {data['titre']}")
                continue

            cours = Cours.objects.create(
                titre=data["titre"],
                description=data["description"],
                niveau=data["niveau"],
                langue="Français",
                prix=data["prix"],
                statut=Cours.Statut.PUBLIE,  # publié directement (contrairement au flux normal formateur -> en_attente -> admin)
                formateur=formateur,
                categorie=categorie,
            )

            cover_path = COVERS_DIR / data["cover"]
            if cover_path.exists():  # ne casse pas la commande si une image de couverture manque sur le disque
                with open(cover_path, "rb") as f:
                    cours.image_couverture.save(data["cover"], File(f), save=True)  # copie le fichier dans MEDIA_ROOT et l'associe au cours

            for ordre_module, module_data in enumerate(data["modules"]):
                module = Module.objects.create(
                    titre=module_data["titre"], ordre=ordre_module, cours=cours  # ordre = position dans la liste (0, 1, 2...)
                )
                for ordre_lecon, (titre, type_contenu, duree) in enumerate(module_data["lecons"]):
                    lecon = Lecon.objects.create(
                        titre=titre,
                        type_contenu=type_contenu,
                        duree_minutes=duree,
                        module=module,
                        ordre=ordre_lecon,
                    )
                    # Vidéo d'exemple (libre de droits) attachée aux leçons vidéo
                    # de démo, pour que le lecteur affiche vraiment un contenu.
                    if type_contenu == "video" and SAMPLE_VIDEO.exists():
                        with open(SAMPLE_VIDEO, "rb") as f:
                            lecon.fichier.save("sample-lesson-video.mp4", File(f), save=True)  # Django renomme automatiquement en cas de collision de nom
                if "quiz" in module_data:  # seul le premier module du cours Django a un quiz dans ces données de démo
                    quiz_data = module_data["quiz"]
                    quiz = Quiz.objects.create(
                        titre=quiz_data["titre"], note_passage=quiz_data["note_passage"], module=module
                    )
                    for ordre_q, (enonce, options) in enumerate(quiz_data["questions"]):
                        question = Question.objects.create(quiz=quiz, enonce=enonce, ordre=ordre_q)
                        for texte, est_correcte in options:
                            ReponseOption.objects.create(
                                question=question, texte=texte, est_correcte=est_correcte
                            )

            self.stdout.write(self.style.SUCCESS(f"Cours créé : {cours.titre} ({cours.categorie.nom})"))  # style.SUCCESS = texte affiché en vert dans le terminal

        self.stdout.write(self.style.SUCCESS("Seed terminé."))
