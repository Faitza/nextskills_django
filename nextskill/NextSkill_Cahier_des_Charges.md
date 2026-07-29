CAHIER DES CHARGES
Projet académique — Framework Django
NextSkill
Plateforme d'Apprentissage en Ligne (E-Learning)
Catalogue des 15 Projets Django — Projet 9
ITAC — Institut de Technologies Appliquées des Cayes
Filière : Développement Web & Mobile
Année académique 2025–2026
Version 1.1 — Juillet 2026

> **Note de version 1.1** : cette version met à jour le document initial (v1.0) pour refléter les choix effectivement retenus pendant l'implémentation — structure réelle des applications Django, modèle `Paiement` finalisé, base de données de la v1, et fonctionnalités ajoutées en cours de développement (gestion de contenu par le formateur, page publique illustrée, tableau de bord administrateur enrichi). Les changements par rapport à la v1.0 sont signalés par « **(v1.1)** » dans le texte.

Table des matières
Table des matières	2
1. Présentation du projet	4
1.1 Contexte	4
1.2 Objectifs du projet	4
1.3 Public cible	4
1.4 Primitives Django attendues	4
2. Acteurs du système	4
3. Spécifications fonctionnelles — Méthode MoSCoW	5
3.1 Must Have (indispensable pour la soutenance)	5
3.2 Should Have (fortement recommandé)	5
3.3 Could Have (bonus, si le temps le permet)	6
3.4 Won't Have (hors périmètre v1)	6
4. Cas d'utilisation	6
4.1 Visiteur (non connecté)	6
4.2 Étudiant	6
4.3 Formateur	7
4.4 Administrateur	7
5. Modèle Conceptuel de Données (MCD)	7
5.1 Entités et attributs principaux	7
Utilisateur	7
Categorie	8
CentreInteret (liaison Étudiant ↔ Categorie)	8
Cours	8
Module	9
Lecon	9
Inscription	9
ProgressionLecon	10
Quiz	10
Question / ReponseOption / TentativeQuiz	10
Avis	10
Panier / LignePanier	11
Paiement	11
5.2 Relations et cardinalités	11
6. Architecture technique	12
6.1 Stack technologique	12
6.2 Structure des applications Django	13
6.3 Sécurité et bonnes pratiques	13
7. Planning prévisionnel (Gantt simplifié)	13
8. Livrables attendus	14
8.1 Documentation	14
8.2 Code source	14
8.3 Soutenance orale	14
8.4 Critères d'évaluation indicatifs	14
9. Budget prévisionnel du projet	15
9.1 Coût de la version de démonstration (v1 — soutenance)	15
9.2 Coût estimé d'une mise en production réelle (post-soutenance)	15
9.3 Justification du choix « coût zéro » pour la v1	16

---

## 1. Présentation du projet

### 1.1 Contexte
NextSkill est une plateforme d'apprentissage en ligne, conçue comme un clone fonctionnel d'outils comme Udemy ou Coursera, adaptée aux exigences académiques du Projet 9 du catalogue de projets Django. Elle permet à des formateurs de publier des cours structurés et à des étudiants de s'y inscrire, de suivre leur progression et de valider leurs acquis par des quiz.

### 1.2 Objectifs du projet
- Démontrer la maîtrise de l'architecture MVT de Django à travers une application multi-rôles.
- Mettre en œuvre un système de contenu pédagogique hiérarchisé (cours → modules → leçons).
- Implémenter un mécanisme fiable de suivi de progression et d'évaluation automatique.
- Respecter les exigences de sécurité, de modélisation de données et de qualité de code définies dans le cahier des charges général des 15 projets.

### 1.3 Public cible
- Étudiants souhaitant suivre des cours en autonomie (vidéo, PDF, quiz).
- Formateurs souhaitant créer et publier du contenu pédagogique structuré.
- Administrateurs assurant la modération et la supervision de la plateforme.

### 1.4 Primitives Django attendues
Conformément aux attentes techniques générales du catalogue : séparation stricte Models / Templates / Views, protection CSRF, hachage des mots de passe via l'ORM Django, base de données relationnelle normalisée, respect de la PEP 8, et historique Git explicite.

## 2. Acteurs du système
Trois rôles distincts sont gérés via un champ « rôle » sur le modèle Utilisateur, avec des permissions et interfaces dédiées. **(v1.1)** L'accès administrateur repose en pratique sur l'indicateur natif Django `is_staff` (positionné par `createsuperuser`) plutôt que sur le champ `role` — un superutilisateur conserve `role="etudiant"` par défaut, ce champ n'étant pas renseigné par `createsuperuser`. Le tableau de bord et les actions d'administration vérifient donc `is_staff`, pas `role == "admin"`.

| Acteur | Description | Permissions principales |
|---|---|---|
| Étudiant | Utilisateur inscrit qui consulte le catalogue, s'inscrit aux cours et suit sa progression. | Parcourir le catalogue, s'inscrire à un cours, visionner les leçons, passer les quiz, consulter sa progression. |
| Formateur | Utilisateur créant et gérant son propre contenu pédagogique. | Créer/modifier/publier des cours, modules et leçons **(vidéo, PDF ou texte, publiées lui-même)**, créer des quiz, consulter les statistiques d'inscription. |
| Administrateur | Superviseur de la plateforme. | Valider/suspendre des cours, gérer les comptes utilisateurs, gérer les catégories, accéder au tableau de bord global. |

## 3. Spécifications fonctionnelles — Méthode MoSCoW

### 3.1 Must Have (indispensable pour la soutenance)
- **Authentification & rôles** — inscription, connexion, déconnexion **(avec confirmation avant déconnexion — v1.1)**, gestion des trois rôles (Étudiant, Formateur, Admin).
- **Gestion des cours** — création de cours par le formateur, organisés en modules et en leçons ordonnées.
- **Contenu multi-format** — support de l'upload et de la lecture de fichiers vidéo et PDF par leçon. **(v1.1)** Le formateur publie lui-même ses leçons (vidéo `.mp4/.mov/.webm`, PDF ou texte) depuis son propre tableau de bord (« Gérer le contenu »), sans passer par l'interface d'administration Django ; le format du fichier est validé côté serveur selon le type de leçon choisi.
- **Inscription aux cours** — un étudiant peut s'inscrire à un cours et accéder à son contenu.
- **Suivi de progression** — marquage d'une leçon comme terminée, calcul automatique du pourcentage de progression par cours.
- **Quiz d'évaluation** — quiz à choix multiples en fin de module, correction automatique, note de passage configurable.
- **Tableau de bord formateur** — liste des cours créés, nombre d'inscrits, taux de complétion, note moyenne, profil (bio, spécialité), et accès direct à la gestion du contenu de chaque cours.
- **Tableau de bord administrateur** — validation des nouveaux cours avant publication, statistiques globales, gestion des utilisateurs. **(v1.1)** Les comptes formateurs et étudiants sont listés séparément ; pour chaque étudiant, le tableau distingue un compte simplement créé d'un compte qui suit activement au moins un cours.
- **Page publique (vitrine)** — accessible sans connexion : Accueil, Services, À propos, Contact, avec accès aux pages Connexion / Inscription. **(v1.1)** Page d'accueil illustrée d'une photo pleine largeur et d'un bandeau de mise en avant (formateurs qualifiés, suivi de progression, paiement flexible) ; page Services illustrée d'une photo par service proposé.
- **Catalogue avec prix et notation** — chaque cours affiche son prix (ou « Gratuit »), la note moyenne sur 5 étoiles et le nombre d'étudiants inscrits. **(v1.1)** Chaque cours publié affiche une photo de couverture dans le catalogue et sur sa page de détail.
- **Profil formateur détaillé** — à l'inscription, le formateur renseigne sa spécialité et une biographie, affichées sur ses cours.
- **Centres d'intérêt à l'inscription** — l'étudiant sélectionne les catégories qui l'intéressent lors de son inscription, pour personnaliser ses recommandations.
- **Panier et paiement fictif** — l'étudiant peut ajouter plusieurs cours à un panier ou acheter directement ; paiement simulé (MonCash, carte bancaire, virement), sans transaction réelle. **(v1.1)** Un achat direct ne retire du panier que le cours effectivement acheté — les autres cours déjà présents dans le panier restent intacts (voir section 5.1, entité Paiement, pour le détail de la modélisation retenue).
- **Sécurité** — protection CSRF, hachage des mots de passe, contrôle d'accès par rôle (decorators Django), confirmation avant les actions destructrices ou de déconnexion.

### 3.2 Should Have (fortement recommandé)
- Catalogue filtrable — recherche et filtres par catégorie **(implémenté — v1.1)**, niveau et langue.
- Certificat de complétion — génération d'un certificat PDF à 100 % de progression. *(non implémenté à ce stade)*
- Reprise de lecture — mémorisation du point d'arrêt vidéo pour chaque étudiant. *(non implémenté à ce stade)*
- Favoris — possibilité de marquer un cours du catalogue comme favori (♡) pour le retrouver plus tard. *(non implémenté à ce stade)*

### 3.3 Could Have (bonus, si le temps le permet)
- Forum de discussion — questions/réponses par cours ou par leçon.
- Recommandations personnalisées — suggestions de cours basées sur les centres d'intérêt choisis à l'inscription.
- Mode hors-ligne partiel — téléchargement des PDF de cours.
- Paiement réel — remplacement du paiement fictif par une véritable passerelle (MonCash API, Stripe…) en post-soutenance.

### 3.4 Won't Have (hors périmètre v1)
- Application mobile native.
- Visioconférence / classes en direct.
- Système de paiement aux formateurs (revenue sharing).

## 4. Cas d'utilisation
Le diagramme de cas d'utilisation UML complet sera fourni dans le rapport de projet (PDF). Le tableau ci-dessous synthétise les cas d'utilisation principaux par acteur, à reporter sur le diagramme.

### 4.1 Visiteur (non connecté)
| Code | Cas d'utilisation | Description |
|---|---|---|
| UC-00 | Consulter la page publique | Parcourir Accueil, Services, À propos et Contact sans compte. |

### 4.2 Étudiant
| Code | Cas d'utilisation | Description |
|---|---|---|
| UC-01 | S'inscrire / se connecter | Créer un compte étudiant (avec sélection des centres d'intérêt) ou se connecter à un compte existant. |
| UC-02 | Parcourir le catalogue | Consulter, filtrer et rechercher des cours disponibles avec prix, photo de couverture et notation. |
| UC-03 | Ajouter au panier / acheter | Ajouter un ou plusieurs cours à un panier, ou acheter directement un cours. |
| UC-03bis | Payer (fictif) | Choisir un mode de paiement simulé (MonCash, carte, virement) et finaliser l'inscription au(x) cours. |
| UC-04 | Suivre une leçon | Visionner une vidéo, consulter un PDF, ou lire une leçon texte. |
| UC-05 | Marquer une leçon terminée | Mettre à jour sa progression dans le cours. |
| UC-06 | Passer un quiz | Répondre à un quiz de fin de module et obtenir un résultat automatique. |
| UC-07 | Consulter sa progression | Visualiser l'avancement global par cours sur un tableau de bord personnel (« Mon apprentissage »). |

### 4.3 Formateur
| Code | Cas d'utilisation | Description |
|---|---|---|
| UC-08 | Compléter son profil | Renseigner sa spécialité et sa biographie, affichées sur ses cours. |
| UC-09 | Créer un cours | Définir titre, description, prix, catégorie, niveau et image de couverture ; le cours est soumis avec le statut « en attente » jusqu'à validation par l'administrateur. |
| UC-10 | Structurer un cours | Ajouter des modules et des leçons ordonnées (vidéo, PDF ou texte), directement depuis son propre tableau de bord — **(v1.1)** sans passer par l'interface d'administration Django. |
| UC-11 | Créer un quiz | Ajouter des questions à choix multiples avec réponses correctes et note de passage. |
| UC-12 | Publier / dépublier un cours | Le cours est publié par validation de l'administrateur (UC-15) ; le formateur ne publie pas directement. |
| UC-13 | Consulter les statistiques | Voir le nombre d'inscrits, le taux de complétion moyen et la note moyenne par cours. |

### 4.4 Administrateur
| Code | Cas d'utilisation | Description |
|---|---|---|
| UC-14 | Gérer les catégories | Créer, modifier ou supprimer les catégories de cours. |
| UC-15 | Valider un cours | Approuver ou rejeter un cours soumis par un formateur avant publication. |
| UC-16 | Gérer les comptes | Suspendre ou réactiver un compte utilisateur. |
| UC-17 | Superviser la plateforme | Accéder au tableau de bord global (utilisateurs, cours, inscriptions, paiements fictifs). **(v1.1)** Formateurs et étudiants sont présentés dans deux tableaux distincts ; pour chaque étudiant, un indicateur précise s'il suit activement un cours ou s'il a seulement créé un compte. |

## 5. Modèle Conceptuel de Données (MCD)
Le schéma entité-association complet (avec cardinalités) sera produit sous forme de diagramme dans le rapport PDF. Les tableaux ci-dessous constituent le dictionnaire de données servant de base à ce diagramme et à l'implémentation des modèles Django.

### 5.1 Entités et attributs principaux

#### Utilisateur
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| username | CharField | Unique, obligatoire (identifiant de connexion) |
| email | EmailField | Obligatoire |
| mot_de_passe | CharField (hash) | Géré par l'ORM Django (PBKDF2) |
| nom, prenom | CharField | Optionnel (`first_name`/`last_name` hérités d'AbstractUser) |
| role | CharField (choices) | etudiant \| formateur \| admin — **(v1.1)** non fiable pour distinguer un compte administrateur : voir section 2 |
| photo_profil | ImageField | Optionnel |
| specialite | CharField | Formateur uniquement — ex : Développement Web |
| bio | TextField | Formateur uniquement — présentation affichée sur ses cours |
| date_inscription | DateTimeField | auto_now_add |

#### Categorie
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| nom | CharField | Unique |
| description | TextField | Optionnel |

#### CentreInteret (liaison Étudiant ↔ Categorie)
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| etudiant (FK) | ForeignKey → Utilisateur | Obligatoire |
| categorie (FK) | ForeignKey → Categorie | Obligatoire |
| unique_together | — | (etudiant, categorie) — sélectionné à l'inscription |

#### Cours
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| titre | CharField | Obligatoire |
| slug | SlugField | Unique, auto-généré |
| description | TextField | Obligatoire |
| prix | DecimalField | 0 = cours gratuit |
| niveau | CharField (choices) | débutant \| intermédiaire \| avancé |
| langue | CharField | Défaut : français |
| image_couverture | ImageField | Optionnel — affichée dans le catalogue et le détail **(v1.1)** |
| statut | CharField (choices) | brouillon \| en_attente \| publié \| rejeté |
| date_creation | DateTimeField | auto_now_add |
| formateur (FK) | ForeignKey → Utilisateur | Obligatoire |
| categorie (FK) | ForeignKey → Categorie | Obligatoire |

#### Module
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| titre | CharField | Obligatoire |
| ordre | PositiveIntegerField | Définit la séquence dans le cours |
| cours (FK) | ForeignKey → Cours | Obligatoire |

#### Lecon
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| titre | CharField | Obligatoire |
| type_contenu | CharField (choices) | video \| pdf \| texte |
| fichier | FileField | Vidéo (.mp4/.mov/.webm) ou PDF selon le type — **(v1.1)** extension validée côté serveur au moment de la publication par le formateur |
| duree_minutes | PositiveIntegerField | Optionnel |
| ordre | PositiveIntegerField | Définit la séquence dans le module |
| module (FK) | ForeignKey → Module | Obligatoire |

#### Inscription
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| etudiant (FK) | ForeignKey → Utilisateur | Obligatoire |
| cours (FK) | ForeignKey → Cours | Obligatoire |
| date_inscription | DateTimeField | auto_now_add |
| progression_pourcentage | DecimalField | Calculé, 0 à 100 |
| statut | CharField (choices) | en_cours \| terminé |
| unique_together | — | (etudiant, cours) — une seule inscription par cours |

#### ProgressionLecon
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| etudiant (FK) | ForeignKey → Utilisateur | Obligatoire |
| lecon (FK) | ForeignKey → Lecon | Obligatoire |
| statut | CharField (choices) | non_commencé \| en_cours \| terminé |
| date_completion | DateTimeField | Null si non terminé |
| unique_together | — | (etudiant, lecon) |

#### Quiz
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| titre | CharField | Obligatoire |
| note_passage | PositiveIntegerField | En pourcentage, défaut 60 |
| module (FK) | OneToOneField → Module | Un quiz par module |

#### Question / ReponseOption / TentativeQuiz
| Entité | Attributs clés | Relation |
|---|---|---|
| Question | enonce (TextField), quiz (FK) | Une question appartient à un seul quiz |
| ReponseOption | texte (CharField), est_correcte (BooleanField), question (FK) | Une option appartient à une seule question |
| TentativeQuiz | etudiant (FK), quiz (FK), score, reussi (BooleanField), date_tentative | Historise chaque tentative d'un étudiant |

#### Avis
| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| etudiant (FK) | ForeignKey → Utilisateur | Obligatoire |
| cours (FK) | ForeignKey → Cours | Obligatoire |
| note | PositiveSmallIntegerField | 1 à 5 étoiles |
| commentaire | TextField | Optionnel |
| date_creation | DateTimeField | auto_now_add |
| unique_together | — | (etudiant, cours) — un seul avis par cours suivi |

#### Panier / LignePanier
| Entité | Attributs clés | Relation |
|---|---|---|
| Panier | etudiant (OneToOne → Utilisateur), date_creation | Un panier actif par étudiant |
| LignePanier | panier (FK), cours (FK), date_ajout | Un cours ajouté au panier d'un étudiant ; unique_together (panier, cours) |

#### Paiement
**(v1.1 — modèle finalisé, différent de l'esquisse initiale de la v1.0)**

| Attribut | Type | Contrainte |
|---|---|---|
| id | AutoField | Clé primaire |
| etudiant (FK) | ForeignKey → Utilisateur | Obligatoire |
| cours (M2M) | ManyToManyField → Cours | Cours couverts par ce paiement — un seul en achat direct, plusieurs lors d'un checkout panier |
| montant | DecimalField | Montant total figé au moment du paiement |
| methode | CharField (choices) | moncash \| carte \| virement |
| statut | CharField (choices) | en_attente \| reussi \| echoue |
| reference_transaction | CharField | Référence fictive générée automatiquement (UUID), unique |
| date_paiement | DateTimeField | auto_now_add |

> **Justification du choix de modélisation (v1.1)** : la v1.0 envisageait un `Paiement` simplement lié à un `montant_total`, sans relation explicite aux cours couverts. En implémentation, un lien direct `Paiement ↔ Cours` (ManyToMany) a été retenu plutôt qu'un lien `Paiement → Panier` : cela permet à un achat direct (hors panier) de ne retirer du panier que le cours réellement acheté, sans jamais vider les autres cours qu'un étudiant y aurait déjà ajoutés. La validation d'un `Paiement` (`Paiement.valider()`) crée les `Inscription` correspondantes puis retire uniquement les `LignePanier` associées aux cours payés.

### 5.2 Relations et cardinalités
| Entité A | Cardinalité | Entité B | Sémantique |
|---|---|---|---|
| Utilisateur (Formateur) | 1,n — 0,n | Cours | Un formateur publie plusieurs cours ; un cours a un seul formateur. |
| Categorie | 1,n — 0,n | Cours | Une catégorie regroupe plusieurs cours. |
| Utilisateur (Étudiant) | 0,n — 0,n | Categorie | Association via CentreInteret, choisi à l'inscription. |
| Cours | 1,1 — 1,n | Module | Un cours contient un ou plusieurs modules, ordonnés. |
| Module | 1,1 — 1,n | Lecon | Un module contient une ou plusieurs leçons, ordonnées. |
| Module | 1,1 — 0,1 | Quiz | Un module possède au plus un quiz d'évaluation. |
| Quiz | 1,1 — 1,n | Question | Un quiz contient une ou plusieurs questions. |
| Question | 1,1 — 2,n | ReponseOption | Une question propose au moins deux options de réponse. |
| Utilisateur (Étudiant) | 0,n — 0,n | Cours | Association via Inscription (table de liaison). |
| Utilisateur (Étudiant) | 0,n — 0,n | Lecon | Association via ProgressionLecon (table de liaison). |
| Utilisateur (Étudiant) | 0,n — 0,n | Quiz | Association via TentativeQuiz (historique des tentatives). |
| Utilisateur (Étudiant) | 0,n — 0,n | Cours | Association via Avis — un étudiant note les cours qu'il suit. |
| Utilisateur (Étudiant) | 1,1 — 0,1 | Panier | Un étudiant possède au plus un panier actif. |
| Panier | 1,1 — 0,n | LignePanier | Un panier contient zéro ou plusieurs lignes (cours ajoutés). |
| LignePanier | 0,n — 1,1 | Cours | Une ligne de panier référence un seul cours. |
| Utilisateur (Étudiant) | 1,n — 0,n | Paiement | Un étudiant peut effectuer plusieurs paiements (un par achat). |
| **Paiement** **(v1.1)** | **0,n — 1,n** | **Cours** | **Association ManyToMany directe — un paiement couvre un ou plusieurs cours, indépendamment du panier.** |

## 6. Architecture technique

### 6.1 Stack technologique
| Couche | Technologie | Justification |
|---|---|---|
| Backend | Django 6.x (Python) | Framework MVT imposé par le cahier des charges général. |
| Base de données | **SQLite (v1 — démonstration) — v1.1** | Base fichier unique, adaptée au développement et à la démonstration académique sans serveur dédié. PostgreSQL reste recommandé pour une mise en production réelle (voir section 9.2). |
| Frontend / Templates | Django Templates + CSS maison (palette bleu marine `#152B54` / orange `#F2662D`) | Rendu côté serveur, cohérent avec la maquette de référence du projet. |
| Gestion des fichiers | Stockage local `/media` (`MEDIA_ROOT`/`MEDIA_URL`) | Stockage des vidéos, PDF de leçons et images de couverture. |
| Lecture vidéo | Balise HTML5 `<video>` | Lecture native, pas de dépendance externe. |
| PDF (certificats) | *Non implémenté à ce stade* | Réservé pour une évolution Should Have (certificat de complétion). |
| Authentification | `django.contrib.auth` (modèle utilisateur personnalisé `accounts.Utilisateur`) | Sécurité éprouvée, hachage natif des mots de passe. |

### 6.2 Structure des applications Django
**(v1.1 — structure effective, mise à jour par rapport à l'esquisse de la v1.0)**

- `accounts/` — modèle Utilisateur personnalisé (AbstractUser + champs `role`, `bio`, `specialite`), modèle `CentreInteret`, inscription (avec centres d'intérêt pour l'étudiant), connexion, déconnexion.
- `courses/` — modèles `Categorie`, `Cours` (avec `prix`, `image_couverture`), `Module`, `Lecon`, `Avis` ; catalogue public et détail de cours ; lecteur de leçon ; **tableau de bord et gestion de contenu du formateur (création de cours, ajout/suppression de modules et leçons) ; tableau de bord et validation des cours de l'administrateur.**
- `enrollments/` — modèles `Inscription` et `ProgressionLecon` ; logique de calcul de progression ; tableau de bord étudiant (« Mon apprentissage »).
- `quizzes/` — modèles `Quiz`, `Question`, `ReponseOption`, `TentativeQuiz` ; passage de quiz et correction automatique.
- `orders/` — modèles `Panier`, `LignePanier`, `Paiement` ; logique d'ajout au panier, achat direct et paiement fictif (MonCash, carte, virement).
- `pages/` — page publique (vitrine) : Accueil, Services, À propos, Contact ; gabarit de base (`base.html`) et feuille de style partagée par tout le site.

> Les tableaux de bord par rôle et les pages transverses ne constituent pas des applications Django séparées (contrairement à l'esquisse `dashboard/`/`core/` de la v1.0) : ils sont rattachés à l'application métier la plus pertinente (`courses/` pour formateur/admin, `enrollments/` pour étudiant, `pages/` pour le contenu public), ce qui évite les imports circulaires entre applications.

### 6.3 Sécurité et bonnes pratiques
- Protection CSRF activée sur tous les formulaires (middleware Django par défaut).
- Contrôle d'accès par rôle via des décorateurs (`@login_required` et vérifications explicites de `role`/`is_staff` en début de vue).
- Validation des types de fichiers uploadés (vidéo/PDF) côté serveur, au niveau du formulaire de publication de leçon.
- Vérification de propriété systématique : un formateur ne peut gérer que les cours dont il est l'auteur (`Cours.objects.get(slug=..., formateur=request.user)`), un étudiant ne peut accéder qu'à ses propres inscriptions/panier.
- Confirmation JavaScript avant déconnexion, et avant toute suppression de module/leçon dans l'espace formateur **(v1.1)**.
- Le module de paiement (`orders/`) est explicitement fictif en v1 : aucune clé API ni transaction réelle ; la validation d'un `Paiement` déclenche directement la création des `Inscription` correspondantes.

## 7. Planning prévisionnel (Gantt simplifié)
Planning indicatif sur 6 semaines, à ajuster selon le calendrier académique fourni par le professeur.

| Semaine | Phase | Livrable intermédiaire |
|---|---|---|
| S1 | Cadrage & conception | Cahier des charges validé, MCD, diagramme de cas d'utilisation. |
| S2 | Mise en place du socle | Projet Django initialisé, modèle Utilisateur, authentification, rôles. |
| S3 | Gestion des cours | Modèles Cours/Module/Leçon, catalogue étudiant, gestion de contenu formateur. |
| S4 | Inscriptions & progression | Inscription aux cours, suivi de progression, lecture vidéo/PDF/texte. |
| S5 | Quiz & tableaux de bord | Quiz à correction automatique, dashboards formateur/admin, panier et paiement fictif. |
| S6 | Finalisation & soutenance | Tests, corrections, rapport PDF, préparation de la démonstration. |

## 8. Livrables attendus

### 8.1 Documentation
- Rapport de projet (PDF) — cahier des charges, diagramme de cas d'utilisation, dictionnaire de données et MCD/UML.
- README.md — instructions d'installation complètes (virtualenv, pip install, migrations, runserver).

### 8.2 Code source
- Dépôt hébergé sur GitHub/GitLab avec historique de commits clair et explicite.
- Code respectant la PEP 8, organisé en applications Django modulaires, commenté ligne par ligne **(v1.1)**.
- **(v1.1)** Commande de gestion `seed_cours_demo` (`python manage.py seed_cours_demo`) : peuple la base avec des formateurs, cours, modules, leçons et un quiz de démonstration, de façon idempotente — utile pour préparer rapidement un environnement de démonstration ou de soutenance.

### 8.3 Soutenance orale
- Démonstration live des fonctionnalités (15 minutes) : parcours étudiant complet, création de cours côté formateur, quiz et tableau de bord.
- Séance de questions techniques (10 minutes).

### 8.4 Critères d'évaluation indicatifs
| Critère | Pondération indicative |
|---|---|
| Fonctionnalités Must Have opérationnelles | 40 % |
| Qualité de la modélisation de données (MCD, normalisation) | 15 % |
| Sécurité (CSRF, hachage, contrôle d'accès) | 15 % |
| Qualité du code et respect de la PEP 8 | 10 % |
| Documentation et README | 10 % |
| Soutenance orale et maîtrise technique | 10 % |

## 9. Budget prévisionnel du projet
En tant que projet académique, NextSkill vise un coût nul pour la version de démonstration (v1, soutenance), en s'appuyant sur des offres gratuites (« free tier »). Le tableau ci-dessous distingue ce coût de démonstration du coût d'une mise en production réelle, pour anticiper les besoins si le projet est poursuivi au-delà du cadre académique.

### 9.1 Coût de la version de démonstration (v1 — soutenance)
| Poste | Solution retenue | Coût |
|---|---|---|
| Hébergement web (serveur Django) | Render / Railway / PythonAnywhere (offre gratuite) | 0 HTG |
| Base de données | SQLite, fichier local inclus dans le projet **(v1.1)** | 0 HTG |
| Nom de domaine | Sous-domaine fourni par l'hébergeur (ex. nextskill.onrender.com) | 0 HTG |
| Certificat SSL (HTTPS) | Let's Encrypt, inclus automatiquement | 0 HTG |
| Stockage médias (vidéos/PDF) | Stockage local du serveur (volume limité) | 0 HTG |
| Passerelle de paiement | Paiement fictif (aucune intégration réelle en v1) | 0 HTG |

Total estimé — v1 (démonstration) : **0 HTG**.

### 9.2 Coût estimé d'une mise en production réelle (post-soutenance)
| Poste | Solution envisagée | Coût estimé (mensuel) |
|---|---|---|
| Hébergement web (VPS) | DigitalOcean / OVH / hébergeur local | 1 000 – 2 500 HTG / mois |
| Base de données PostgreSQL | Migration recommandée de SQLite vers une instance gérée (Render Pro, Supabase, ElephantSQL payant) **(v1.1)** | 500 – 1 200 HTG / mois |
| Nom de domaine (.com ou .ht) | Registrar (Namecheap, ou NIC Haïti pour .ht) | 1 500 – 5 000 HTG / an |
| Stockage médias (cloud) | Cloudinary / AWS S3 (selon volume de vidéos) | 500 – 1 500 HTG / mois |
| Passerelle de paiement réelle | API MonCash (frais transactionnels par paiement) | Variable — frais au % par transaction |
| Maintenance / nom de domaine renouvelé | Suivi technique, sauvegardes | À définir selon convention |

Total estimé — production réelle (usage modéré, hors frais transactionnels) : environ 2 000 à 5 000 HTG par mois, hors coût annuel du nom de domaine.

### 9.3 Justification du choix « coût zéro » pour la v1
- Le projet est réalisé dans un cadre académique, sans budget alloué par l'établissement.
- Les offres gratuites des hébergeurs (Render, Railway, PythonAnywhere) suffisent pour une démonstration et une soutenance, avec des limites acceptables (mise en veille après inactivité, stockage limité).
- SQLite évite la dépendance à un serveur de base de données externe pendant le développement et la démonstration, tout en restant un choix migrable vers PostgreSQL sans changement de modèles (l'ORM Django abstrait le moteur de base de données) **(v1.1)**.
- Le paiement fictif permet de démontrer le flux complet (panier, choix du mode de paiement, confirmation) sans nécessiter l'ouverture d'un compte marchand MonCash ou Stripe, laquelle exige une immatriculation d'entreprise et des frais que le projet académique ne peut engager.
