# apps/amoamancustom/amoamancustom/setup/erpnext_pricing.py
"""
Amorce les trois offres tarifaires affichées sur /erpnext/tarification.

Même mécanique que setup/email_templates.py : le fichier est la référence
d'installation, la base est la vérité d'exécution. `installer()` ne crée une
offre que si elle est absente ; une offre retouchée depuis le Desk (prix,
fonctionnalités, mise en avant) n'est jamais réécrite par une migration
ultérieure. C'est précisément l'intérêt de sortir ce contenu du template : le
marketing ajuste sans développeur.

    bench --site <site> execute amoamancustom.setup.erpnext_pricing.etat
        rapport sans écriture (PRESENTE / ABSENTE, nb de fonctionnalités)

    bench --site <site> execute amoamancustom.setup.erpnext_pricing.reinitialiser
        force fichier -> base (repart des valeurs de la maquette)

Les montants proviennent de la maquette Figma (layer 3586:1447). Ils sont
affichés tels quels, sans formatage monétaire : « Sur Devis » doit pouvoir
occuper la même place que « 300.000 ».
"""

import frappe

DOCTYPE = "ERPNext Pricing Plan"

OFFRES = [
	{
		"plan_name": "Essentiel",
		"tagline": "ERPNext Basique + FNE intégrée",
		"audience": "Parfait pour les TPE",
		"users_label": "Nombre illimité d'utilisateurs",
		"price_label": "100.000",
		"price_suffix": "FCFA / Mois",
		"is_featured": 0,
		"cta_label": "Commencer",
		"features": [
			"Comptabilité",
			"Achats",
			"Ventes",
			"Stocks",
			"POS +2",
			"Intégration des moyens de paiement",
			"Formation des utilisateurs",
			"Sécurité",
			"Support basique",
		],
	},
	{
		"plan_name": "Business",
		"tagline": "ERPNext Modules avancés + FNE intégrée",
		"audience": "Parfait pour les PME",
		"users_label": "Nombre illimité d'utilisateurs",
		"price_label": "300.000",
		"price_suffix": "FCFA / Mois",
		"is_featured": 1,
		"cta_label": "Commencer",
		"features": [
			"Toute l'offre Essentiel",
			"Analyse & Cadrage personnalisés",
			"Workflows personnalisés",
			"Reprise de données",
			"Tableaux de bord personnalisés avec Insight",
			"Doctype formulaire",
			"Documentation Guide utilisateur - paramétrage",
			"POS +2",
			"Site web",
			"CRM",
			"RH",
			"Paie",
			"Immos",
			"Prêts",
			"Intégration des moyens de paiement",
		],
	},
	{
		"plan_name": "Entreprise",
		"tagline": "ERPNext Complet avec Personnalisation par module + FNE intégrée",
		"audience": "Parfait pour les entreprises déjà matures & digitalisées",
		"users_label": "Nombre illimité d'utilisateurs",
		"price_label": "Sur Devis",
		"price_suffix": "uniquement",
		"is_featured": 0,
		"cta_label": "Commencer",
		"features": [
			"Toute l'offre BUSINESS",
			"Développement de module personnalisé",
			"Création d'application spécifique sur le Framework Frappe",
			"UX/UI design personnalisé",
			"Intégration API",
			"BI & Reporting avancé",
			"Hébergement",
			"Support avec SLA + Haute Disponibilité + formation utilisateurs",
		],
	},
]


def installer():
	"""Point d'entrée appelé par `after_migrate`. Idempotent."""
	if not frappe.db.exists("DocType", DOCTYPE):
		return

	crees = []

	for index, offre in enumerate(OFFRES, start=1):
		if frappe.db.exists(DOCTYPE, offre["plan_name"]):
			continue

		_creer(offre, index)
		crees.append(offre["plan_name"])

	if crees:
		frappe.db.commit()
		print(f"Offres tarifaires créées : {', '.join(crees)}")


def _creer(offre, index):
	doc = frappe.new_doc(DOCTYPE)
	doc.plan_name = offre["plan_name"]
	doc.tagline = offre["tagline"]
	doc.audience = offre["audience"]
	doc.users_label = offre["users_label"]
	doc.price_label = offre["price_label"]
	doc.price_suffix = offre["price_suffix"]
	doc.is_featured = offre["is_featured"]
	doc.cta_label = offre["cta_label"]
	doc.cta_href = "/erpnext/contact"
	doc.published = 1
	doc.idx = index

	for label in offre["features"]:
		doc.append("features", {"label": label, "included": 1})

	doc.insert(ignore_permissions=True)


def reinitialiser():
	"""Force fichier -> base : supprime les trois offres et les recrée.

	À n'utiliser que pour repartir des valeurs de la maquette : toute retouche
	faite dans le Desk est perdue.
	"""
	for offre in OFFRES:
		if frappe.db.exists(DOCTYPE, offre["plan_name"]):
			frappe.delete_doc(DOCTYPE, offre["plan_name"], force=True, ignore_permissions=True)
			print(f"  ✗ {offre['plan_name']} supprimée")

	frappe.db.commit()
	installer()


def etat():
	"""Rapport sans écriture."""
	if not frappe.db.exists("DocType", DOCTYPE):
		print(f"DocType {DOCTYPE} absent : lancer `bench migrate`.")
		return

	print("=== Offres tarifaires ERPNext ===")

	for offre in OFFRES:
		nom = offre["plan_name"]

		if not frappe.db.exists(DOCTYPE, nom):
			print(f"  ABSENTE   {nom}")
			continue

		doc = frappe.get_doc(DOCTYPE, nom)
		publiee = "publiée" if doc.published else "DÉPUBLIÉE"
		mise_en_avant = ", mise en avant" if doc.is_featured else ""
		print(
			f"  PRÉSENTE  {nom:12} {doc.price_label} {doc.price_suffix} — "
			f"{len(doc.features)} fonctionnalités ({publiee}{mise_en_avant})"
		)

	autres = frappe.get_all(
		DOCTYPE,
		filters={"plan_name": ("not in", [o["plan_name"] for o in OFFRES])},
		pluck="name",
	)

	if autres:
		print(f"  + {len(autres)} offre(s) ajoutée(s) hors maquette : {', '.join(autres)}")
