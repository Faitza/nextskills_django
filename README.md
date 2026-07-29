# NextSkill — Contexte du projet

## Vue d'ensemble

NextSkill est une plateforme d'apprentissage en ligne (e-learning), **Projet 9** d'un catalogue de 15 projets académiques Django, réalisé à l'**ITAC** (Institut de Technologies Appliquées des Cayes, Haïti).

Le cahier des charges complet est dans `NextSkill_Cahier_des_Charges.docx` à la racine du projet — **le lire en premier** avant toute modification structurelle importante.

## Stack technique

- Django 5.x (Python), architecture MVT stricte
- PostgreSQL (voir `settings_extrait.py` pour la config `AUTH_USER_MODEL`)
- Templates Django + Bootstrap 5 (pas de framework JS lourd)
- Paiement **fictif uniquement** en v1 (MonCash, carte, virement — simulés, aucune vraie transaction)

## Rôles (3 acteurs)

- **Étudiant** — parcourt le catalogue, achète/panier, suit les cours, passe les quiz, note les cours (1-5 étoiles), choisit des centres d'intérêt à l'inscription
- **Formateur** — crée des cours (avec prix), renseigne une bio + spécialité à l'inscription, consulte ses statistiques
- **Administrateur** — valide les cours avant publication, tableau de bord global (inclus en v1, décision confirmée)

## Applications Django (5)

- `accounts/` — Utilisateur personnalisé (AbstractUser + role, bio, specialite), inscription avec centres d'intérêt
- `courses/` — Categorie, Cours (avec `prix`), Module, Lecon, Avis (notation 1-5 étoiles)
- `enrollments/` — Inscription, ProgressionLecon (calcul auto de la progression)
- `quizzes/` — Quiz, Question, ReponseOption, TentativeQuiz (correction automatique)
- `orders/` — **à créer** : Panier, LignePanier, Paiement (fictif)

Les `models.py` de `accounts`, `courses`, `enrollments`, `quizzes` existent déjà dans ce dossier. **`orders/` reste à créer** avec les modèles `Panier`, `LignePanier`, `Paiement` (voir section 5.1 du cahier des charges — entités Panier/LignePanier/Paiement).

À ajouter dans `courses/models.py` : le champ `prix` (DecimalField, 0 = gratuit) sur `Cours`, et le modèle `Avis` (etudiant FK, cours FK, note 1-5, commentaire, unique_together etudiant+cours).

À ajouter dans `accounts/models.py` : `CentreInteret` (liaison Utilisateur ↔ Categorie de `courses`, choisi à l'inscription étudiant) — attention à l'import circulaire, `Categorie` vit dans `courses`.

## Décisions déjà prises (ne pas re-proposer)

- Dashboard Administrateur : **inclus** en v1 (validation cours + stats globales)
- Paiement : **fictif** en v1 — décision motivée par contrainte budgétaire (pas de compte marchand MonCash/Stripe réel possible pour un projet académique sans immatriculation d'entreprise). Voir section 9 du cahier des charges pour le détail budgétaire.
- Panier ET achat direct : les deux flux coexistent (choix libre de l'étudiant)
- Palette visuelle (démo HTML) : bleu marine (#152B54) + orange (#F2662D) — voir `NextSkill_Demo.html` comme référence visuelle si des templates doivent s'en inspirer
- Page publique (avant connexion) : Accueil / Services / À propos / Contact, sans données personnelles

## Fichiers de référence dans ce dossier

- `NextSkill_Cahier_des_Charges.docx` — cahier des charges complet (MoSCoW, cas d'utilisation, MCD, architecture, budget)
- `NextSkill_Demo.html` — maquette HTML interactive (référence visuelle uniquement, pas du code Django)
- `README_MODELES.md` — logique de conception des modèles existants
- `settings_extrait.py` — config `AUTH_USER_MODEL` et `INSTALLED_APPS`

## Préférences de travail

- Toujours donner du code complet et fonctionnel, pas de fragments partiels
- Expliquer brièvement le "pourquoi" des choix techniques (pas juste le code)
- Respecter la PEP 8
- Français dans les commentaires, noms de modèles/champs et messages utilisateur
