# Amoaman Custom App

Personnalisations ERPNext/HRMS pour **AMOAMAN & ASSOCIES** : RH, facturation, site web, paie et intégrations métier.

---

## Fonctionnalités

| Module | Contenu |
|--------|---------|
| **RH** | Ancienneté auto, validation présence, gestion congés, notes de frais personnalisées |
| **Facturation** | Formats d'impression (facture, commande, devis, BL, timesheet), calcul jours travaillés |
| **Paie** | Slip de salaire personnalisé, structures salariales adaptées |
| **Site web** | Pages événements, formulaire contact, partenaires, thème CSS AMOAMAN |
| **LinkedIn** | Cache API LinkedIn (rafraîchi toutes les heures) |
| **Rappels** | Rappel de marquage de présence automatique à 08h00 |
| **Notifications** | Override du centre de notifications Frappe |
| **Prêts** | Workflow et boutons personnalisés sur Loan Application |

---

## Prérequis

- Frappe Framework ≥ 15
- ERPNext installé
- HRMS installé
- Lending installé (pour les modules prêts)

---

## Installation

```bash
# 1. Récupérer l'app
bench get-app amoamancustom https://github.com/AMOAMAN/amoamancustom

# 2. Installer sur le site
bench --site <nom_du_site> install-app amoamancustom

# 3. Migrer (applique custom fields, workflows, fixtures)
bench --site <nom_du_site> migrate

# 4. Construire les assets JS/CSS
bench build --app amoamancustom

# 5. Redémarrer
bench restart
```

---

## Configuration

### 1. Société

Vérifier dans **ERPNext → Société** que `AMOAMAN & ASSOCIES` est correctement configurée (compte bancaire, adresse, paramètres fiscaux).

### 2. LinkedIn Settings

Aller dans **Amoaman Custom App → LinkedIn Settings** :

| Champ | Description |
|-------|-------------|
| Client ID | ID application LinkedIn |
| Client Secret | Secret application LinkedIn |
| Access Token | Token OAuth LinkedIn |

### 3. Rappels de présence

Configuré automatiquement via scheduler (cron `0 8 * * *`).  
Pour désactiver : commenter la ligne dans `hooks.py → scheduled_jobs`.

### 4. Formats d'impression

Les formats sont dans : **Paramètres → Print Format**

Formats disponibles :
- `Facture Print` — Sales Invoice
- `Commande Print` — Sales Order
- `Devis Print` — Quotation
- `Delivery Note Print` — Delivery Note
- `Timesheet Print` — Timesheet
- `Slip de Salaire` — Salary Slip

---

## Mise à jour des fixtures

Après modification de Custom Fields, Workflows ou Property Setters :

```bash
bench --site <nom_du_site> export-fixtures --app amoamancustom
git add amoamancustom/fixtures/
git commit -m "chore: mise à jour fixtures"
```

---

## Désinstallation

```bash
bench --site <nom_du_site> uninstall-app amoamancustom
bench --site <nom_du_site> migrate
bench build
```

---

## Licence

MIT — AMOAMAN & ASSOCIES
