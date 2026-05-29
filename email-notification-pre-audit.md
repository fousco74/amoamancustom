# Notification Email — Data Compliance Pre Audit

## Email Metadata

| Champ | Valeur |
|---|---|
| `email_subject` | `Nouveau pré-audit reçu — {{ company_name }}` |
| `email_preheader` | `{{ contact_person }} ({{ role }}) a soumis un questionnaire de conformité. Réf : {{ doc_name }}.` |
| `email_from_name` | `Amoaman & Associés — Conformité` |
| `email_from_address` | `conformite@amoaman.ci` |
| `email_to` | `audit@amoaman.ci` |
| `email_cc` | *(vide — ou responsable conformité secondaire)* |
| `email_reply_to` | `{{ email }}` |
| `email_category` | `Notification` |
| `email_priority` | `Normal` |

---

## Email Body — Sections & Field Mapping

### Bannière alerte (hero block)

| Token | Valeur |
|---|---|
| `hero_icon` | `📋` |
| `hero_tag` | `Pré-audit — Loi 2013-450` |
| `hero_title` | `Nouveau questionnaire soumis` |
| `hero_subtitle` | `{{ company_name }} vient de compléter le pré-audit de conformité. {{ answered_count }}/15 questions répondue(s).` |

### Bloc référence

| Token | Valeur |
|---|---|
| `ref_label` | `Référence` |
| `ref_value` | `{{ doc_name }}` (ex: DCPA.2026.00001) |
| `date_label` | `Date de soumission` |
| `date_value` | `{{ submission_date }}` (format long : 26 mai 2026 à 14:30) |
| `status_label` | `Statut` |
| `status_value` | `Nouveau` (badge coloré) |

### Bloc entreprise

| Token | Label | Champ réel |
|---|---|---|
| `block_title` | `Informations entreprise` | — |
| `row_company_name` | `Entreprise` | `company_name` |
| `row_sector` | `Secteur` | `sector` |
| `row_company_size` | `Effectif` | `company_size` |
| `row_contact_person` | `Contact` | `contact_person` |
| `row_role` | `Fonction` | `role` |
| `row_email` | `Email` | `email` |
| `row_phone` | `Téléphone` | `phone` |

### Bloc score rapide (mini dashboard)

| Token | Label | Calcul |
|---|---|---|
| `score_oui` | `✅ Conformité (Oui)` | Nombre de réponses `"Oui"` sur 15 |
| `score_non` | `❌ Non-conformité (Non)` | Nombre de réponses `"Non"` sur 15 |
| `score_nsp` | `❓ Incertain (NSP)` | Nombre de réponses `"NSP"` sur 15 |
| `score_pct` | `Taux de conformité` | `(oui_count / 15) * 100`, affiché en % |
| `score_bar` | `Barre de progression` | Largeur = `score_pct`%, couleur verte/rouge selon score |
| `score_verdict` | `Verdict rapide` | Si `score_pct >= 70` → "Profil favorable" / si `>= 40` → "Risque modéré" / sinon → "Alerte — Risque élevé" |

### Bloc réponses détaillées

| Token | Valeur |
|---|---|
| `answers_table_title` | `Détail des 15 questions` |
| `answers_table_cols` | `N°` / `Question` / `Réponse` / `Commentaire` |
| `answers_row_n` | `question_number` |
| `answers_row_q` | `question` (texte complet) |
| `answers_row_r` | `response` (Oui → badge vert / Non → badge rouge / NSP → badge violet) |
| `answers_row_c` | `client_comment` (si vide → `—`) |

### Bloc questions critiques (alertes)

| Token | Valeur |
|---|---|
| `critical_title` | `Points d'attention immédiats` |
| `critical_desc` | `Questions répondues "Non" ou "NSP" — actions prioritaires.` |
| `critical_list` | Boucle sur `answers` où `response IN ("Non", "NSP")`, afficher `question_number`. `question` + badge `response` |

### Call-to-action principal

| Token | Valeur |
|---|---|
| `cta_label` | `Voir le dossier complet` |
| `cta_url` | `{{ frappe.utils.get_url() }}/app/data-compliance-pre-audit/{{ doc_name }}` |
| `cta_secondary_label` | `Attribuer à un analyste` |
| `cta_secondary_url` | `{{ frappe.utils.get_url() }}/app/data-compliance-pre-audit/{{ doc_name }}` |

### Footer

| Token | Valeur |
|---|---|
| `footer_text` | `Cet email est une notification automatique générée par la plateforme Amoaman & Associés. Le rapport personnalisé sera envoyé au client ({{ email }}) sous 24 à 48 heures ouvrables après analyse.` |
| `footer_brand` | `Amoaman & Associés — Conseil en conformité & protection des données personnelles` |
| `footer_logo_url` | `{{ frappe.utils.get_url() }}/assets/amoamancustom/images/logo.webp` |
| `footer_website` | `https://amoaman.ci` |
| `footer_contact` | `contact@amoaman.ci` |

---

## Design Tokens (UI/UX)

| Token | Valeur |
|---|---|
| `color_primary` | `#266BCC` (bleu marque) |
| `color_accent` | `#F32A57` (rose/rouge marque) |
| `color_success` | `#16a34a` (vert — réponses Oui) |
| `color_danger` | `#dc2626` (rouge — réponses Non) |
| `color_warning` | `#9333ea` (violet — réponses NSP) |
| `color_bg` | `#f8f9ff` (fond clair) |
| `color_text` | `#081A2A` (texte principal) |
| `color_muted` | `#6b7280` (texte secondaire) |
| `font_family` | `Montserrat, -apple-system, Segoe UI, sans-serif` |
| `border_radius` | `12px` (cards), `8px` (badges) |
| `spacing_unit` | `8px` (multiples de 8) |

---

## Règles conditionnelles d'affichage

| Condition | Comportement |
|---|---|
| `sector` est vide | Masquer la ligne Secteur |
| `phone` est vide | Masquer la ligne Téléphone |
| `role` est vide | Afficher `—` |
| `company_size` est vide | Afficher `Non précisée` |
| `client_comment` est vide | Afficher `—` en gris clair |
| `answered_count < 15` | Afficher un avertissement : `⚠️ Questionnaire incomplet — {{ 15 - answered_count }} question(s) sans réponse.` |
| `score_pct <= 30` | Ajouter le tag `🔴 Urgent` dans le hero |

---

## Résumé des sections de l'email (ordre)

1. **Hero** — Titre + sous-titre + référence + date
2. **Score** — Barre visuelle Oui/Non/NSP + taux de conformité + verdict
3. **Entreprise** — Tableau 2 colonnes : infos société + infos contact
4. **Points d'attention** — Liste des réponses Non/NSP (si existantes)
5. **Détail complet** — Tableau des 15 questions avec réponse + commentaire
6. **CTA** — Bouton Voir le dossier + Attribuer à un analyste
7. **Footer** — Logo + mention automatique + contact cabinet
