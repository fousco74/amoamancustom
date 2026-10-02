# apps/amoamancustom/amoamancustom/contact_api.py
"""
Endpoint du formulaire de contact du mini-site ERPNext (/erpnext/contact).

Chaque demande crée un **Lead** (CRM ERPNext), et non plus un `Contact Us` :
le prospect entre directement dans le pipeline commercial, avec ses modules
cochés, son secteur et son besoin rangés dans les Custom Field du Lead — ceux
du formulaire historique « Besoins ERP », que lit déjà la notification
« Lead mail notification » (site_web/notification/lead_mail_notification.py).

Pourquoi un module dédié plutôt que `amoamancustom.api.create_entry` :
`create_entry` (api.py:982) est `allow_guest=True`, accepte **n'importe quel
doctype** transmis par le client et insère en `ignore_permissions=True`. Un
visiteur anonyme peut donc y créer un `User`, un `ToDo` ou une `Lead`. C'est
une élévation de privilèges, et c'est ce que le formulaire historique /contact
utilise aujourd'hui. On ne la propage pas au nouveau formulaire.

Ce module suit le modèle de `pre_audit_api.py` : doctype en dur, liste blanche
de champs, assainissement et validation côté serveur, valeurs de liste
contraintes.

Protection anti-spam, absente partout ailleurs dans l'app :
  - un champ leurre (`site_web`) que seuls les robots remplissent ;
  - une limite de trois envois par heure et par IP, via le cache Redis.

La protection CSRF est assurée par Frappe dès lors que l'appel passe par
`frappe.call` (en-tête X-Frappe-CSRF-Token).

Les Custom Field du Lead ne sont pas versionnés (le dossier fixtures/ est
absent, voir CLAUDE.md) : sur un site qui ne les a pas, `frappe.get_doc` ignore
les clés inconnues et le Lead est créé avec ses seuls champs standard.
"""

import re

import frappe
from frappe import _
from frappe.utils import strip_html_tags

DOCTYPE = "Lead"

# Origine posée sur chaque Lead du formulaire. Elle sert de filtre dans la
# liste des Leads et déclenche « Lead mail notification », dont la condition
# (`doc.custom_logiciel_ or doc.utm_source == ...`) ne reconnaissait jusque-là
# que le formulaire historique. Créée à la volée si absente : simple Link.
SOURCE_UTM = "Site web ERPNext"

# Valeur du Custom Field `custom_service` (Select ERPnext/GRC/IRIXFLOW).
SERVICE = "ERPnext"

# Longueur maximale par champ saisi, alignée sur le type de colonne cible.
CHAMPS = {
	"first_name": 140,
	"entreprise": 140,
	"taille_entreprise": 20,
	"secteur_activite": 140,
	"email": 140,
	"number": 40,
	"indicatif": 2,
	"message": 4000,
}

CHAMPS_REQUIS = ("first_name", "email", "number", "entreprise", "message")

# (valeur stockée, libellé affiché). Les valeurs sont celles du Select standard
# `Lead.no_of_employees` (erpnext/crm/doctype/lead/lead.json) : toute autre
# valeur ferait échouer l'insertion sur la validation du Select.
TAILLES = (
	("1-10", "1 à 10 salariés"),
	("11-50", "11 à 50 salariés"),
	("51-200", "51 à 200 salariés"),
	("201-500", "201 à 500 salariés"),
	("501-1000", "501 à 1 000 salariés"),
	("1000+", "Plus de 1 000 salariés"),
)

# Champ Select du secteur ; ses options sont lues en base (voir secteurs()).
CHAMP_SECTEUR = "custom_secteur_dactivité"

# Module affiché dans le formulaire -> case à cocher du Lead. Plusieurs
# libellés peuvent viser la même case (Ventes et CRM partagent « Ventes & CRM »).
MODULES = {
	"Comptabilité": "custom_comptabilité__finance",
	"Achats": "custom_achats",
	"Production": "custom_gestion_de_la_production",
	"Projets": "custom_projet",
	"Ventes": "custom_ventes__crm",
	"CRM": "custom_ventes__crm",
	"Stocks": "custom_gestion_des_stocks",
	"Qualité": "custom_qualité",
	"RH & Paie": "custom_ressources_humaines___paie",
	"Support": "custom_assistance_support",
	"Immos": "custom_immobilisation",
	"Points de vente": "custom_point_de_vente",
}

CHAMP_BESOIN = "custom_décrivez_brièvement_votre_besoin_ou_vos_attentes"
CHAMP_CONSENTEMENT = "custom_consentement_traitement_donnees"

# Indicatif proposé par défaut, puis pays placés en tête de liste : les deux
# implantations du cabinet (Abidjan, Dakar).
PAYS_DEFAUT = "ci"
PAYS_EN_TETE = ("ci", "sn")

# Anti-spam
CHAMP_LEURRE = "site_web"
LIMITE_PAR_HEURE = 3
PREFIXE_CACHE = "erpx_contact:"



def _message_succes():
	# Fonction et non constante : _() doit être évalué dans la langue de la
	# requête, pas à l'import du module.
	return _("Merci, votre demande a bien été envoyée. Notre équipe vous recontacte rapidement.")


class SaisieInvalide(Exception):
	"""Erreur à afficher telle quelle au visiteur, sous le formulaire.

	On ne passe pas par `frappe.throw` : sur le site public, `frappe.call`
	ouvrirait une modale msgprint (frappe/website/js/website.js:153) en plus du
	message du formulaire.
	"""


def secteurs():
	"""Options du Select `custom_secteur_dactivité` : [(valeur, libellé)].

	Lues dans la méta plutôt que recopiées ici : une option ajoutée ou renommée
	dans le Custom Field apparaît dans le formulaire sans toucher au code, et le
	serveur ne peut jamais proposer une valeur que le Select refuserait. Les
	options en base portent des espaces irréguliers (« Commerce /Distribution ») :
	seul le libellé est normalisé, la valeur reste exacte.
	"""
	champ = frappe.get_meta(DOCTYPE).get_field(CHAMP_SECTEUR)
	if not champ:
		return []

	options = [o.strip() for o in (champ.options or "").split("\n") if o.strip()]
	return [(o, re.sub(r"\s*/\s*", " / ", o)) for o in options]


def _assainir(valeur, longueur_max):
	"""Texte brut : balises retirées, espaces rognés, tronqué. Jamais None.

	Pas d'échappement HTML ici : la valeur part dans un champ du Lead, lu dans
	le Desk, où « A &amp; B » s'afficherait tel quel. C'est au rendu (mail de
	notification) d'échapper.
	"""
	if valeur is None:
		return ""

	return strip_html_tags(str(valeur)).strip()[:longueur_max]


def _email_valide(email):
	"""Validation volontairement simple : on refuse l'absurde, pas le rare."""
	return bool(re.match(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$", email))


def _drapeau(iso):
	"""Émoji drapeau d'un code ISO 3166 à deux lettres (« ci » -> 🇨🇮).

	Pas d'image : 245 pays, aucun fichier à servir. Windows n'a pas de glyphes
	de drapeaux et affiche les deux lettres (« CI ») : repli lisible.
	"""
	return "".join(chr(0x1F1E6 + ord(c) - ord("a")) for c in iso.lower())


def indicatifs():
	"""[{"iso", "nom", "isd", "drapeau"}] pour la liste des indicatifs.

	Source : frappe/geo/country_info.json (clé `isd`), le référentiel que Frappe
	utilise déjà pour les pays. Les noms y sont en anglais (« Ivory Coast ») :
	on les traduit par Babel, déjà présent avec Frappe, dans la langue de la
	requête. Les 5 territoires sans `isd` sont écartés.
	"""
	from babel import Locale
	from frappe.geo.country_info import get_all

	try:
		territoires = Locale.parse(frappe.local.lang or "fr", sep="-").territories
	except Exception:
		territoires = Locale("fr").territories

	pays = []
	for nom, info in get_all().items():
		iso, isd = (info.get("code") or "").lower(), info.get("isd")
		if len(iso) != 2 or not isd:
			continue
		pays.append({
			"iso": iso,
			"nom": territoires.get(iso.upper(), nom),
			"isd": isd,
			"drapeau": _drapeau(iso),
		})

	en_tete = [p for code in PAYS_EN_TETE for p in pays if p["iso"] == code]
	reste = sorted((p for p in pays if p["iso"] not in PAYS_EN_TETE), key=lambda p: p["nom"])
	return en_tete + reste


def _normaliser_telephone(numero, pays):
	"""(« 06 12 34 56 78 », « fr ») -> « +33612345678 » (format E.164).

	L'indicatif est choisi dans la liste (`pays`, code ISO) ; un numéro déjà
	saisi au format international (« +221 77… ») l'emporte sur la liste.

	Le découpage est confié à `phonenumbers` (dépendance de Frappe, déjà utilisée
	par validate_phone_number_with_country_code) : lui seul sait que le 0 initial
	est un préfixe national à retirer en France, mais fait partie du numéro en
	Côte d'Ivoire depuis 2021. On n'exige qu'un numéro *possible* (longueur
	plausible pour le pays), pas *valide* : une plage récemment ouverte serait
	sinon refusée tant que la bibliothèque n'est pas à jour.

	E.164 tient en 16 caractères : sous la limite de 20 de PHONE_NUMBER_PATTERN
	(frappe/utils/__init__.py:45), que `mobile_no` (Data/Phone) doit respecter.
	"""
	import phonenumbers

	pays = (pays or PAYS_DEFAUT).lower()
	if pays not in {p["iso"] for p in indicatifs()}:
		raise SaisieInvalide(_("L'indicatif pays sélectionné n'est pas reconnu."))

	try:
		analyse = phonenumbers.parse(numero, pays.upper())
	except phonenumbers.NumberParseException:
		analyse = None

	if not analyse or not phonenumbers.is_possible_number(analyse):
		raise SaisieInvalide(_("Le numéro de téléphone saisi n'est pas valide."))

	return phonenumbers.format_number(analyse, phonenumbers.PhoneNumberFormat.E164)


def _ip_client():
	return frappe.local.request_ip or "inconnue"


def _verifier_frequence():
	"""Trois envois par heure et par IP. Lève SaisieInvalide au-delà."""
	cle = PREFIXE_CACHE + _ip_client()
	envois = frappe.cache().get_value(cle) or 0

	if int(envois) >= LIMITE_PAR_HEURE:
		raise SaisieInvalide(_("Vous avez déjà envoyé plusieurs demandes. Merci de réessayer dans une heure."))

	frappe.cache().set_value(cle, int(envois) + 1, expires_in_sec=3600)


def _source_utm():
	"""Garantit l'existence de la UTM Source du formulaire, et la retourne."""
	if not frappe.db.exists("UTM Source", SOURCE_UTM):
		frappe.get_doc({"doctype": "UTM Source", "name": SOURCE_UTM}).insert(
			ignore_permissions=True, set_name=SOURCE_UTM
		)
	return SOURCE_UTM


def _valider(data):
	"""Retourne (valeurs assainies, modules retenus). Lève SaisieInvalide."""
	valeurs = {champ: _assainir(data.get(champ), longueur) for champ, longueur in CHAMPS.items()}

	if any(not valeurs[champ] for champ in CHAMPS_REQUIS):
		raise SaisieInvalide(_("Merci de renseigner tous les champs obligatoires."))

	if not _email_valide(valeurs["email"]):
		raise SaisieInvalide(_("L'adresse e-mail saisie n'est pas valide."))

	valeurs["number"] = _normaliser_telephone(valeurs["number"], valeurs.pop("indicatif"))

	if valeurs["taille_entreprise"] and valeurs["taille_entreprise"] not in dict(TAILLES):
		raise SaisieInvalide(_("La taille d'entreprise sélectionnée n'est pas reconnue."))

	if valeurs["secteur_activite"] and valeurs["secteur_activite"] not in dict(secteurs()):
		raise SaisieInvalide(_("Le secteur d'activité sélectionné n'est pas reconnu."))

	# `services` arrive sous forme de liste de modules cochés.
	modules = data.get("services") or []
	if isinstance(modules, str):
		modules = [modules]

	modules = [m for m in (_assainir(m, 60) for m in modules) if m in MODULES]
	if not modules:
		raise SaisieInvalide(_("Merci de sélectionner au moins un module."))

	return valeurs, modules


def _recapitulatif(valeurs, modules):
	"""Texte de la demande, pour le commentaire posé sur un Lead existant."""
	lignes = [
		_("Nouvelle demande reçue via le formulaire /erpnext/contact."),
		_("Nom : {0}").format(valeurs["first_name"]),
		_("Entreprise : {0}").format(valeurs["entreprise"]),
		_("Téléphone : {0}").format(valeurs["number"]),
		_("Modules : {0}").format(", ".join(modules)),
		_("Message : {0}").format(valeurs["message"]),
	]
	return "<br>".join(frappe.utils.escape_html(ligne) for ligne in lignes)


@frappe.whitelist(allow_guest=True)
def submit_contact(data):
	"""Crée un Lead à partir du formulaire. Retourne {"ok", "message"}.

	`data` est un dict (ou son JSON) dont seules les clés de CHAMPS, `services`
	et `accept` sont lues : tout le reste est ignoré en silence, y compris un
	`doctype` que le client tenterait d'imposer.

	Les erreurs de saisie reviennent en {"ok": 0, "message": ...} (HTTP 200)
	pour être affichées sous le formulaire ; seules les erreurs imprévues
	remontent en exception.
	"""
	data = frappe.parse_json(data) if isinstance(data, str) else (data or {})

	if not isinstance(data, dict):
		return {"ok": 0, "message": _("Données invalides.")}

	# 1. Piège à robots : rempli => on répond comme si tout allait bien, sans
	#    rien écrire. Un message d'erreur renseignerait l'automate.
	if _assainir(data.get(CHAMP_LEURRE), 100):
		return {"ok": 1, "message": _message_succes()}

	try:
		# 2. Validation avant la limite de fréquence : une faute de frappe ne
		#    doit pas consommer l'un des trois envois de l'heure.
		valeurs, modules = _valider(data)
		_verifier_frequence()
	except SaisieInvalide as e:
		return {"ok": 0, "message": str(e)}

	# 3. Consentement : obligatoire côté formulaire, revérifié ici.
	if data.get("accept") not in (1, "1", True, "true", "on"):
		return {"ok": 0, "message": _("Merci d'accepter l'utilisation de vos données pour être recontacté(e).")}

	# 4. Email déjà connu : Lead.check_email_id_is_unique
	#    (erpnext/crm/doctype/lead/lead.py:151) refuserait un second Lead, et
	#    son message cite le Lead existant — un lien du Desk qu'un visiteur n'a
	#    pas à voir. On rattache la nouvelle demande au Lead existant, en
	#    commentaire, et on répond comme pour une création.
	existant = frappe.db.get_value(DOCTYPE, {"email_id": valeurs["email"]})
	if existant:
		frappe.get_doc(DOCTYPE, existant).add_comment(
			"Comment", _recapitulatif(valeurs, modules), comment_email=valeurs["email"]
		)
		return {"ok": 1, "message": _message_succes()}

	lead = {
		"doctype": DOCTYPE,
		"first_name": valeurs["first_name"],
		"email_id": valeurs["email"],
		"mobile_no": valeurs["number"],
		"company_name": valeurs["entreprise"],
		"no_of_employees": valeurs["taille_entreprise"] or None,
		"request_type": "Product Enquiry",
		"utm_source": _source_utm(),
		"custom_service": SERVICE,
		CHAMP_SECTEUR: valeurs["secteur_activite"],
		CHAMP_BESOIN: valeurs["message"],
		CHAMP_CONSENTEMENT: 1,
	}
	lead.update({MODULES[m]: 1 for m in modules})

	doc = frappe.get_doc(lead)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {"ok": 1, "name": doc.name, "message": _message_succes()}


@frappe.whitelist(allow_guest=True)
def options():
	"""Listes de référence du formulaire, pour éviter de les dupliquer côté page."""
	return {
		"tailles": TAILLES,
		"secteurs": secteurs(),
		"modules": list(MODULES),
		"indicatifs": indicatifs(),
	}
