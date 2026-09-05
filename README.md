# IMACID Logistics Performance

Application web de **gestion, d'analyse et de suivi des performances des fournisseurs
de transport et de transit**, développée dans le cadre du stage :

> **« Optimisation des coûts de transport et de transit à travers le suivi des
> performances des fournisseurs »** — IMACID / Groupe OCP.

---

## 1. Architecture générale

```
             ┌─────────────────────────┐
             │       UTILISATEUR       │
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │       FRONTEND          │
             │ HTML + Bootstrap 5 + JS │
             │       Chart.js          │
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │         DJANGO          │
             │ Gestion + KPI + Analyse │
             └───────┬─────────┬───────┘
                     │         │
             ┌───────▼───┐ ┌──▼─────────┐
             │  SQLite / │ │Pandas/NumPy│
             │ PostgreSQL│ │  Analyse   │
             └───────────┘ └────────────┘
                     │
                     ▼
             ┌─────────────────────────┐
             │ Dashboard & Aide à la   │
             │ décision logistique     │
             └─────────────────────────┘
```

**Stack technique :**
- Backend : Python 3.11+ / Django 5
- Frontend : HTML5, Bootstrap 5, JavaScript, Chart.js
- Base de données : SQLite par défaut (fonctionne immédiatement), PostgreSQL en option
- Analyse de données : Pandas, NumPy
- Export : CSV, Excel (openpyxl / xlsxwriter)

---

## 2. Modèle de données

```
Supplier (Fournisseur)
   │
   ├── Order (Commande)
   │      │
   │      ├── Transport   (1 commande → plusieurs transports)
   │      ├── Transit     (1 commande → plusieurs opérations de transit)
   │      └── Dispute     (Litige, optionnel)
   │
   └── ActionPlan (Plan d'action correctif)

Cause (référentiel des causes de surcoût / retard, réutilisé par Transit et Dispute)
```

Toutes les relations sont des `ForeignKey` Django classiques (`on_delete=CASCADE` pour
les entités dépendant strictement d'une commande, `SET_NULL` pour les causes).

---

## 3. Arborescence du projet

```
imacid_logistics/
│
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── config/                    # Configuration du projet
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── dashboard/                  # Application principale
│   ├── models.py                # Supplier, Order, Transport, Transit, Dispute, Cause, ActionPlan
│   ├── views.py                  # Dashboard, CRUD, KPI, analyses, import/export
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── services.py               # Calcul des KPI et du score fournisseur
│   ├── templatetags/
│   │   └── dashboard_extras.py
│   └── management/commands/
│       ├── seed_data.py            # Données de démonstration (fictives)
│       ├── import_historical.py    # Import des données réelles 2026
│       └── create_test_accounts.py # Comptes de test (admin / gestionnaire / utilisateur)
│
├── templates/
│   ├── dashboard/                # Toutes les pages de l'application
│   └── registration/login.html
│
├── static/
│   ├── css/style.css
│   └── js/dashboard.js
│
└── media/
```

---

## 4. Installation (Windows / VS Code)

Ouvrez un terminal dans le dossier du projet (`imacid_logistics/`) et exécutez :

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> Si `pip install` échoue sur `psycopg2-binary`, ignorez-le : PostgreSQL est **optionnel**,
> l'application fonctionne nativement avec SQLite (aucune installation supplémentaire requise).

---

## 5. Lancer le projet

```bash
python manage.py migrate
python manage.py create_test_accounts
python manage.py import_historical
python manage.py seed_data
python manage.py runserver
```

Puis ouvrez : **http://127.0.0.1:8000/**

---

## 6. Comptes de test

| Rôle            | Utilisateur    | Mot de passe  | Accès                                  |
|-----------------|----------------|---------------|-----------------------------------------|
| Administrateur  | `admin`        | `admin123`    | Accès complet + `/admin/` Django        |
| Gestionnaire    | `gestionnaire` | `gestion123`  | Gestion des données + consultation KPI  |
| Utilisateur     | `utilisateur`  | `user123`     | Consultation dashboard et données       |

---

## 7. Données

- `python manage.py import_historical` importe les **10 commandes réelles** du rapport
  *"Données Historiques 2026"* fourni par l'entreprise (marquées `Réel` dans l'interface).
- `python manage.py seed_data` génère des **données fictives** supplémentaires afin de
  disposer d'un volume suffisant pour tester les graphiques et les analyses (marquées
  `Démo` dans l'interface — clairement distinguées des données réelles).
- La page **Import Excel** (`/import-excel/`) permet d'importer vos propres fichiers
  Excel de commandes historiques. Colonnes obligatoires : `number`, `supplier_code`,
  `order_date`, `planned_date`, `planned_cost`.

---

## 8. Fonctionnalités principales

- **Dashboard** : KPI cards, filtres dynamiques, 11 graphiques Chart.js (évolution des
  coûts, coût prévu vs réel, retards par fournisseur, OTD, score fournisseurs,
  répartition des causes, top 5 performants / top 5 surcoûts...)
- **Commandes / Transport / Transit / Litiges** : CRUD complet (ajouter, modifier,
  supprimer, consulter, rechercher, filtrer)
- **Fournisseurs** : fiche détaillée avec KPI individuels et score de performance
- **KPI** : OTD, taux de retard, écart de coût, taux de surcoût, coût moyen, taux de
  litiges, score fournisseur (pondération configurable dans `settings.SCORE_WEIGHTS`)
- **Analyse des surcoûts / retards** : tableaux détaillés + répartition par cause
- **Classement des fournisseurs** : 🟢 Excellent / 🟡 Moyen / 🔴 À améliorer
- **Recommandations** : générées automatiquement à partir des seuils KPI réels
- **Plan d'action** : suivi des actions correctives avec taux d'avancement global
- **Import Excel** avec détection d'erreurs et aperçu des données
- **Export** CSV (commandes) et Excel (KPI)
- **Authentification** à 3 niveaux (Administrateur / Gestionnaire / Utilisateur)

---

## 9. Utiliser PostgreSQL (optionnel)

Par défaut, l'application utilise SQLite. Pour passer à PostgreSQL, définissez ces
variables d'environnement avant de lancer les commandes `migrate` / `runserver` :

```bash
set USE_POSTGRES=True
set DB_NAME=imacid_logistics
set DB_USER=postgres
set DB_PASSWORD=votre_mot_de_passe
set DB_HOST=localhost
set DB_PORT=5432
```

Puis décommentez `psycopg2-binary` dans `requirements.txt` et réinstallez les
dépendances (`pip install -r requirements.txt`).

---

## 10. Vérification finale / points à adapter

- Les données réelles importées (`import_historical`) ne contiennent pas de coût
  "réel" distinct du coût "prévu" dans le rapport source : les deux sont donc
  identiques pour ces 10 commandes. Dès que vous disposerez de données réelles
  incluant un écart prévu/réel, importez-les via la page **Import Excel** pour
  activer pleinement l'analyse des surcoûts.
- Le score fournisseur utilise une approximation de la "qualité de service" basée
  sur le taux de retard ; vous pouvez l'enrichir avec vos propres critères qualité
  dans `dashboard/services.py::compute_supplier_score`.
- Pensez à changer `DJANGO_SECRET_KEY` et à désactiver `DEBUG` avant toute mise en
  production réelle.
