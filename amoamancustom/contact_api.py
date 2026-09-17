# apps/amoamancustom/amoamancustom/contact_api.py
"""
Endpoint du formulaire de contact du mini-site ERPNext (/erpnext/contact).

Pourquoi un module dédié plutôt que `amoamancustom.api.create_entry` :
`create_entry` (api.py:982) est `allow_guest=True`, accepte **n'importe quel
doctype** transmis par le client et insère en `ignore_permissions=True`. Un
visiteur anonyme peut donc y créer un `User`, un `ToDo` ou une `Lead`. C'est
une élévation de privilèges, et c'est ce que le formulaire historique /contact
utilise aujourd'hui. On ne la propage pas au nouveau formulaire.

Ce module suit le modèle de `pre_audit_api.py`, qui est la bonne référence du
dépôt : doctype en dur, liste blanche de champs, assainissement et validation
côté serveur, valeurs de liste contraintes.

Protection anti-spam, absente partout ailleurs dans l'app :
  - un champ leurre (`site_web`) que seuls les robots remplissent ;
  - une limite de trois envois par heure et par IP, via le cache Redis.

La protection CSRF est assurée par Frappe dès lors que l'appel passe par
`frappe.call` (en-tête X-Frappe-CSRF-Token).
"""

import html
import re

import frappe
from frappe import _

DOCTYPE = "Contact Us"

# Longueur maximale par champ, alignée sur le type de colonne : Data = 140,
# Small Text et Long Text sont plus permissifs mais rien ne justifie d'accepter
# un roman dans un formulaire de contact.
CHAMPS = {
	"first_name": 140,
	"last_name": 140,
	"entreprise": 140,
	"taille_entreprise": 140,
	"secteur_activite": 140,
	"email": 140,
	"number": 40,
	"services": 500,
	"message": 4000,
}

CHAMPS_REQUIS = ("first_name", "email", "number", "entreprise", "message")

# Valeurs proposées par les listes déroulantes du formulaire. Le serveur les
# contraint : une valeur absente est rejetée plutôt que stockée telle quelle.
TAILLES = (
	"1 à 9 salariés",
	"10 à 49 salariés",
	"50 à 249 salariés",
	"250 salariés et plus",
)

SECTEURS = (
	"Production",
	"Commerce et distribution",
	"Vente au détail",
	"Commerce électronique",
	"Éducation",
	"Soins de santé",
	"Services professionnels",
	"Autre",
)

MODULES = (
	"Comptabilité",
	"Achats",
	"Production",
	"Projets",
	"Ventes",
	"CRM",
	"Stocks",
	"Qualité",
	"RH & Paie",
	"Support",
	"Immos",
	"Points de vente",
)

# Anti-spam
CHAMP_LEURRE = "site_web"
LIMITE_PAR_HEURE = 3
PREFIXE_CACHE = "erpx_contact:"


def _assainir(valeur, longueur_max):
	"""Échappe le HTML et tronque. Retourne une chaîne, jamais None."""
	if valeur is None:
		return ""

	return html.escape(str(valeur).strip())[:longueur_max]


def _email_valide(email):
	"""Validation volontairement simple : on refuse l'absurde, pas le rare."""
	return bool(re.match(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$", email))


def _ip_client():
	return frappe.local.request_ip or "inconnue"


def _verifier_frequence():
	"""Trois envois par heure et par IP. Lève une exception au-delà."""
	cle = PREFIXE_CACHE + _ip_client()
	envois = frappe.cache().get_value(cle) or 0

	if int(envois) >= LIMITE_PAR_HEURE:
		frappe.throw(
			_("Vous avez déjà envoyé plusieurs demandes. Merci de réessayer dans une heure."),
			title=_("Trop de demandes"),
		)

	frappe.cache().set_value(cle, int(envois) + 1, expires_in_sec=3600)


@frappe.whitelist(allow_guest=True)
def submit_contact(data):
	"""Enregistre une demande de contact. Retourne {"name": ...}.

	`data` est un dict (ou son JSON) dont seules les clés de CHAMPS sont lues :
	tout le reste est ignoré en silence, y compris un `doctype` que le client
	tenterait d'imposer.
	"""
	data = frappe.parse_json(data) if isinstance(data, str) else (data or {})

	if not isinstance(data, dict):
		frappe.throw(_("Données invalides."))

	# 1. Piège à robots : rempli => on répond comme si tout allait bien, sans
	#    rien écrire. Un message d'erreur renseignerait l'automate.
	if _assainir(data.get(CHAMP_LEURRE), 100):
		return {"name": None, "message": _("Merci, votre demande a bien été envoyée.")}

	# 2. Limite de fréquence par IP.
	_verifier_frequence()

	# 3. Liste blanche + assainissement.
	valeurs = {
		champ: _assainir(data.get(champ), longueur) for champ, longueur in CHAMPS.items()
	}

	# 4. Champs obligatoires.
	manquants = [champ for champ in CHAMPS_REQUIS if not valeurs[champ]]
	if manquants:
		frappe.throw(_("Merci de renseigner tous les champs obligatoires."))

	# 5. Email.
	if not _email_valide(valeurs["email"]):
		frappe.throw(_("L'adresse e-mail saisie n'est pas valide."))

	# 6. Valeurs de liste contraintes.
	if valeurs["taille_entreprise"] and valeurs["taille_entreprise"] not in TAILLES:
		frappe.throw(_("La taille d'entreprise sélectionnée n'est pas reconnue."))

	if valeurs["secteur_activite"] and valeurs["secteur_activite"] not in SECTEURS:
		frappe.throw(_("Le secteur d'activité sélectionné n'est pas reconnu."))

	# `services` arrive sous forme de liste de modules cochés.
	modules = data.get("services") or []
	if isinstance(modules, str):
		modules = [modules]

	modules = [m for m in (_assainir(m, 60) for m in modules) if m in MODULES]
	valeurs["services"] = ", ".join(modules)

	# 7. Consentement : case à cocher, stockée telle quelle.
	accept = 1 if data.get("accept") in (1, "1", True, "true", "on") else 0

	doc = frappe.get_doc({"doctype": DOCTYPE, **valeurs, "accept": accept})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"name": doc.name,
		"message": _("Merci, votre demande a bien été envoyée. Notre équipe vous recontacte rapidement."),
	}


@frappe.whitelist(allow_guest=True)
def options():
	"""Listes de référence du formulaire, pour éviter de les dupliquer côté page."""
	return {"tailles": TAILLES, "secteurs": SECTEURS, "modules": MODULES}
