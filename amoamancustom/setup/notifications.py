# apps/amoamancustom/amoamancustom/setup/notifications.py
"""
Notifications d'Amoaman & Associés : francise les mails, neutralise les doublons
anglais livrés par HRMS/ERPNext, et répare les notifications cassées.

Deux couches, comme pour email_templates.py :

  1. Six notifications anglaises standard sont DÉSACTIVÉES (pas supprimées :
     on ne touche pas aux apps standard, on ne fait qu'un UPDATE du champ
     `enabled` en base). Chacune est remplacée par un équivalent français qui
     étend `_base_mail.html` et porte un bouton vers le document concerné.

  2. Les notifications françaises déjà en base mais défaillantes sont corrigées :
       - « Contrat proche expiration » référençait `doc.contract_end_date` et
         `doc.employee_name`, deux champs qui n'existent pas sur le doctype
         Contract (CRM) ; la condition ne matche donc jamais. On passe sur
         `doc.end_date` / `doc.party_name`.
       - « Demande de congés - en attente RH MAIL » avait son HTML enveloppé de
         backticks (rendu en code brut). On réécrit le message proprement.
       - « Validation Demande de congés » avait un double espace dans le sujet.
       - « New HD ticket » envoyait le placeholder « Add your message here » en
         cloche seule. On réécrit en français et on passe en Email + cloche.
       - « Contact Notification » et « Notifications candidat » n'étaient que des
         cloches (System Notification) sans lien. On les passe en Email + cloche.
       - « Inscription confirmée - Webinaire » avait son destinataire en `cc`
         seulement : un envoi sans « To » ne part pas. On pointe le champ `email`.
       - « Alerte fin de contrat » (event Method, method NULL) est supprimée :
         elle ne peut jamais se déclencher et fait doublon avec
         « Contrat proche expiration ».

Tout est IDEMPOTENT : `installer()` est rejoué à chaque `bench migrate`. Les
correctifs ne s'appliquent que si la valeur en base est encore celle du bug
(voir `etat()`), de sorte qu'une retouche faite dans l'interface n'est jamais
écrasée par une migration ultérieure.

Le tout via `frappe.db.set_value` (et jamais `doc.save()` sur un enregistrement
`is_standard = 1`) : set_value ne déclenche ni `on_update` ni
`export_module_json`, donc aucune écriture dans `apps/` — la règle « ne pas
modifier les apps standard » reste intacte.
"""

import frappe

GABARIT = "amoamancustom/templates/emails/_base_mail.html"
COMPOSANTS = "amoamancustom/templates/emails/_composants.html"

ENTETE = '{{% extends "{gabarit}" %}}\n{{% import "{composants}" as ui %}}\n'.format(
	gabarit=GABARIT, composants=COMPOSANTS
)


# ---------------------------------------------------------------------------
# 1. Notifications anglaises standard à neutraliser (remplacées ci-dessous).
# ---------------------------------------------------------------------------
NOTIFICATIONS_A_DESACTIVER = (
	"Exit Interview Scheduled",
	"Training Scheduled",
	"Training Feedback",
	"Retention Bonus",
	"Material Request Receipt Notification",
	"Notification for new fiscal year",
)


# ---------------------------------------------------------------------------
# 2. Les six remplacements français.
# ---------------------------------------------------------------------------
# Chaque entrée : nom, module, et un dictionnaire de champs. Le message est un
# gabarit Jinja complet (extends _base_mail.html). `creer_si_absent` ne le pose
# que s'il n'existe pas déjà.
NOTIFICATIONS = [
	{
		"nom": "Entretien de départ programmé",
		"module": "HR_CUSTOM",
		"champs": {
			"channel": "Email",
			"event": "Days Before",
			"document_type": "Exit Interview",
			"date_changed": "date",
			"days_in_advance": 1,
			"condition_type": "Python",
			"condition": "doc.date and doc.email and doc.docstatus != 2 and doc.status == 'Scheduled'",
			"subject": "Entretien de départ : {{ doc.employee_name }} ({{ frappe.utils.formatdate(doc.date) }})",
			"message_type": "HTML",
			"message": ENTETE + """

{% set soustitre = doc.company %}
{% set mention_pied = "Cet entretien fait partie du processus de départ." %}

{% block titre %}Entretien de départ programmé{% endblock %}
{% block preheader %}Un entretien de départ est programmé pour {{ doc.employee_name }}.{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("Un entretien de départ est programmé pour " ~ doc.employee_name ~ ".") }}
{{ ui.details([
  ("Collaborateur", doc.employee ~ " — " ~ doc.employee_name),
  ("Date", frappe.utils.formatdate(doc.date)),
  ("Société", doc.company),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Ouvrir l'entretien") }}
{% endblock %}
""",
		},
		"recipients": [{"receiver_by_document_field": "email"}],
	},
	{
		"nom": "Formation programmée",
		"module": "HR_CUSTOM",
		"champs": {
			"channel": "Email",
			"event": "Submit",
			"document_type": "Training Event",
			"condition_type": "Python",
			"condition": "",
			"subject": "Formation programmée : {{ doc.event_name }}",
			"message_type": "HTML",
			"message": ENTETE + """

{% set soustitre = doc.location %}
{% set mention_pied = "Vous recevez ce message car vous êtes inscrit à cette formation." %}

{% block titre %}Formation programmée{% endblock %}
{% block preheader %}La formation « {{ doc.event_name }} » est programmée.{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("La formation « " ~ doc.event_name ~ " » est programmée. Voici les informations utiles.") }}
{{ ui.details([
  ("Formation", doc.event_name),
  ("Lieu", doc.location),
  ("Début", frappe.utils.format_datetime(doc.start_time)),
  ("Fin", frappe.utils.format_datetime(doc.end_time)),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Voir la formation") }}
{% endblock %}
""",
		},
		"recipients": [{"receiver_by_document_field": "employee_emails"}],
	},
	{
		"nom": "Partagez votre avis sur la formation",
		"module": "HR_CUSTOM",
		"champs": {
			"channel": "Email",
			"event": "Submit",
			"document_type": "Training Result",
			"condition_type": "Python",
			"subject": "Votre avis sur la formation {{ doc.training_event }}",
			"message_type": "HTML",
			"message": ENTETE + """

{% set soustitre = doc.training_event %}
{% set mention_pied = "Votre retour nous aide à améliorer nos formations." %}

{% block titre %}Partagez votre avis sur la formation{% endblock %}
{% block preheader %}Merci de partager votre retour sur la formation {{ doc.training_event }}.{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("Merci de partager votre retour sur la formation « " ~ doc.training_event ~ " ».") }}
{{ ui.p("Votre avis nous aide à améliorer la qualité de nos formations.") }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Donner mon avis") }}
{% endblock %}
""",
		},
		"recipients": [{"receiver_by_document_field": "employee_emails"}],
	},
	{
		"nom": "Prime de fidélisation à venir",
		"module": "payroll_custom",
		"champs": {
			"channel": "Email",
			"event": "Days Before",
			"document_type": "Retention Bonus",
			"date_changed": "bonus_payment_date",
			"days_in_advance": 14,
			"condition_type": "Python",
			"condition": "doc.docstatus == 1",
			"subject": "Prime de fidélisation à venir : {{ doc.employee_name }}",
			"message_type": "HTML",
			"message": ENTETE + """

{% set soustitre = doc.department %}
{% set mention_pied = "Cette prime sera due à la date indiquée ci-dessous." %}

{% block titre %}Prime de fidélisation à venir{% endblock %}
{% block preheader %}Une prime de fidélisation est due pour {{ doc.employee_name }}.{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("Une prime de fidélisation est due pour " ~ doc.employee_name ~ ".") }}
{{ ui.details([
  ("Employé", doc.employee_name),
  ("Date de versement", frappe.utils.formatdate(doc.bonus_payment_date)),
  ("Société", doc.company),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Ouvrir la prime") }}
{% endblock %}
""",
		},
		"recipients": [{"receiver_by_role": "HR Manager"}],
	},
	{
		"nom": "Demande de matériel reçue",
		"module": "Amoaman Custom App",
		"champs": {
			"channel": "Email",
			"event": "Value Change",
			"document_type": "Material Request",
			"value_changed": "status",
			"condition_type": "Python",
			"condition": "doc.status == \"Received\" or doc.status == \"Partially Received\"",
			"subject": "Demande de matériel reçue : {{ doc.name }}",
			"message_type": "HTML",
			"message": ENTETE + """

{% set soustitre = doc.material_request_type %}
{% set mention_pied = "Cette demande de matériel a été marquée comme reçue." %}

{% block titre %}Demande de matériel reçue{% endblock %}
{% block preheader %}La demande {{ doc.name }} a été reçue.{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("La demande de matériel " ~ doc.name ~ " a été reçue.") }}
{{ ui.details([
  ("Type de demande", doc.material_request_type),
  ("Société", doc.company),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Ouvrir la demande") }}
{% endblock %}
""",
		},
		"recipients": [{"receiver_by_document_field": "owner"}],
	},
	{
		"nom": "Nouvel exercice fiscal",
		"module": "Amoaman Custom App",
		"champs": {
			"channel": "Email",
			"event": "New",
			"document_type": "Fiscal Year",
			"condition_type": "Python",
			"condition": "doc.auto_created == 1",
			"subject": "Nouvel exercice fiscal : {{ doc.name }}",
			"message_type": "HTML",
			"message": ENTETE + """

{% set soustitre = "Exercice fiscal" %}
{% set mention_pied = "Cet exercice a été créé automatiquement." %}

{% block titre %}Nouvel exercice fiscal{% endblock %}
{% block preheader %}Un nouvel exercice fiscal a été créé : {{ doc.name }}.{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("Un nouvel exercice fiscal a été créé automatiquement.") }}
{{ ui.details([
  ("Exercice", doc.name),
  ("Début", frappe.utils.formatdate(doc.year_start_date)),
  ("Fin", frappe.utils.formatdate(doc.year_end_date)),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Ouvrir l'exercice") }}
{% endblock %}
""",
		},
		"recipients": [
			{"receiver_by_role": "Accounts Manager"},
			{"receiver_by_role": "Accounts User"},
		],
	},
]


# ---------------------------------------------------------------------------
# 3. Correctifs des notifications françaises déjà en base.
# ---------------------------------------------------------------------------
def installer():
	"""Point d'entrée appelé par `after_migrate`. Idempotent."""
	desactiver_anglaises()

	for notification in NOTIFICATIONS:
		creer_si_absent(notification)

	corriger_francaises()
	supprimer_alerte_fin_contrat()

	frappe.client_cache.delete_keys("notifications::")
	frappe.db.commit()


def desactiver_anglaises():
	"""Coupe les six notifications anglaises standard, sans les supprimer."""
	for nom in NOTIFICATIONS_A_DESACTIVER:
		if not frappe.db.exists("Notification", nom):
			continue
		if frappe.db.get_value("Notification", nom, "enabled"):
			frappe.db.set_value("Notification", nom, "enabled", 0)


def creer_si_absent(notification: dict) -> bool:
	"""Crée la notification française si elle n'existe pas. Ne réécrit jamais."""
	if frappe.db.exists("Notification", notification["nom"]):
		return False

	doc = frappe.new_doc("Notification")
	doc.name = notification["nom"]
	doc.module = notification["module"]
	for champ, valeur in notification["champs"].items():
		setattr(doc, champ, valeur)
	for destinataire in notification.get("recipients", []):
		# dict() : _init_child ajoute "doctype" au dict qu'on lui passe ; sans la
		# copie, on muterait les données de NOTIFICATIONS (effet de bord).
		doc.append("recipients", dict(destinataire))
	doc.insert(ignore_permissions=True)
	return True


def corriger_francaises():
	"""Applique les correctifs, uniquement si la valeur en base est encore cassée."""
	corriger_contrat()
	corriger_conges()
	corriger_hd_ticket()
	convertir_cloches_en_email()
	corriger_inscription()


def corriger_contrat():
	"""« Contrat proche expiration » : champs erronés + lien manquant."""
	nom = "Contrat proche expiration"
	if not frappe.db.exists("Notification", nom):
		return

	condition = frappe.db.get_value("Notification", nom, "condition") or ""
	sujet = frappe.db.get_value("Notification", nom, "subject") or ""
	message = frappe.db.get_value("Notification", nom, "message") or ""

	if "contract_end_date" in condition:
		frappe.db.set_value(
			"Notification",
			nom,
			"condition",
			'doc.status == "Active" and doc.end_date and doc.party_type == "Employee"',
		)

	if "employee_name" in sujet:
		frappe.db.set_value(
			"Notification", nom, "subject", "Contrat proche expiration - {{ doc.party_name }}"
		)

	if GABARIT not in message:
		frappe.db.set_value("Notification", nom, "message", _message_contrat())
		frappe.db.set_value("Notification", nom, "message_type", "HTML")


def corriger_conges():
	"""Les trois mails de congé : gabarit commun, lien, et bugs de forme."""
	corrections = {
		"Demande de congés - en attente DG MAIL": _message_conge_validation(
			"Demande de congé à valider",
			"Une demande de congé de {{ doc.employee_name }} attend votre approbation.",
			"Demande de congé à valider",
			"Valider la demande",
		),
		"Demande de congés - en attente RH MAIL": _message_conge_validation(
			"Demande de congé à valider",
			"Une demande de congé de {{ doc.employee_name }} attend votre validation.",
			"Demande de congé à valider",
			"Valider la demande",
		),
		"Validation Demande de congés": _message_conge_approuve(),
	}

	for nom, message in corrections.items():
		if not frappe.db.exists("Notification", nom):
			continue
		en_base = frappe.db.get_value("Notification", nom, "message") or ""
		if GABARIT not in en_base:
			frappe.db.set_value("Notification", nom, "message", message)
			frappe.db.set_value("Notification", nom, "message_type", "HTML")

	# Sujet à double espace : « ... }}  - En attente de validation DG ».
	nom_validation = "Validation Demande de congés"
	sujet = frappe.db.get_value("Notification", nom_validation, "subject") or ""
	if "  - En attente" in sujet:
		frappe.db.set_value(
			"Notification",
			nom_validation,
			"subject",
			sujet.replace("  - En attente", " - En attente"),
		)


def corriger_hd_ticket():
	"""« New HD ticket » : placeholder anglais, cloche seule -> Email + cloche."""
	nom = "New HD ticket"
	if not frappe.db.exists("Notification", nom):
		return

	message = frappe.db.get_value("Notification", nom, "message") or ""
	if GABARIT not in message:
		frappe.db.set_value("Notification", nom, "message", _message_hd_ticket())
		frappe.db.set_value("Notification", nom, "message_type", "HTML")

	if frappe.db.get_value("Notification", nom, "channel") != "Email":
		frappe.db.set_value("Notification", nom, "channel", "Email")
		frappe.db.set_value("Notification", nom, "send_system_notification", 1)


def convertir_cloches_en_email():
	"""Cloches seules -> Email + cloche, avec lien, pour contact et candidat."""
	conversions = {
		"Contact Notification": _message_contact(),
		"Notifications candidat": _message_candidat(),
	}

	for nom, message in conversions.items():
		if not frappe.db.exists("Notification", nom):
			continue
		en_base = frappe.db.get_value("Notification", nom, "message") or ""
		if GABARIT not in en_base:
			frappe.db.set_value("Notification", nom, "message", message)
			frappe.db.set_value("Notification", nom, "message_type", "HTML")

		if frappe.db.get_value("Notification", nom, "channel") != "Email":
			frappe.db.set_value("Notification", nom, "channel", "Email")
			frappe.db.set_value("Notification", nom, "send_system_notification", 1)


def corriger_inscription():
	"""« Inscription confirmée - Webinaire » : destinataire réel (champ email)."""
	nom = "Inscription confirmée - Webinaire"
	if not frappe.db.exists("Notification", nom):
		return

	lignes = frappe.get_all(
		"Notification Recipient",
		filters={"parent": nom, "parentfield": "recipients"},
		fields=["name", "receiver_by_document_field"],
	)
	for ligne in lignes:
		if ligne.receiver_by_document_field != "email":
			frappe.db.set_value(
				"Notification Recipient", ligne.name, "receiver_by_document_field", "email"
			)
			frappe.db.set_value("Notification Recipient", ligne.name, "cc", None)


def supprimer_alerte_fin_contrat():
	"""« Alerte fin de contrat » : event Method sans method, jamais déclenchable."""
	nom = "Alerte fin de contrat"
	if frappe.db.exists("Notification", nom):
		frappe.delete_doc("Notification", nom, ignore_permissions=True, force=True)


# ---------------------------------------------------------------------------
# Messages de correction (gabarit commun + bouton vers le document).
# ---------------------------------------------------------------------------
def _message_contrat():
	return ENTETE + """

{% set soustitre = doc.party_name %}
{% set mention_pied = "Merci de prendre les dispositions nécessaires (renouvellement ou fin de contrat)." %}

{% block titre %}Contrat bientôt expiré{% endblock %}
{% block preheader %}Le contrat de {{ doc.party_name }} arrive à expiration.{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("Le contrat de " ~ doc.party_name ~ " arrive à expiration.") }}
{{ ui.details([
  ("Partie", doc.party_name),
  ("Type de partie", doc.party_type),
  ("Référence", doc.name),
  ("Date de fin", frappe.utils.formatdate(doc.end_date)),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Ouvrir le contrat") }}
{% endblock %}
"""


def _message_conge_validation(titre, preheader, titre_bloc, libelle_bouton):
	return ENTETE + """

{% set soustitre = doc.department %}
{% set mention_pied = "Vous recevez ce message car une demande de congé attend votre validation." %}

{% block titre %}{TITRE}{% endblock %}
{% block preheader %}{PREHEADER}{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("Une demande de congé de " ~ doc.employee_name ~ " (" ~ doc.department ~ ") est en attente de validation.") }}
{{ ui.details([
  ("Collaborateur", doc.employee_name ~ " (" ~ doc.employee ~ ")"),
  ("Période", "Du " ~ frappe.utils.formatdate(doc.from_date) ~ " au " ~ frappe.utils.formatdate(doc.to_date)),
  ("Nombre de jours", doc.total_leave_days),
  ("Type de congé", doc.leave_type),
  ("Motif", doc.description),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "BOUTON") }}
{% endblock %}
""".replace("{TITRE}", titre).replace("{PREHEADER}", preheader).replace("BOUTON", libelle_bouton)


def _message_conge_approuve():
	return ENTETE + """

{% set soustitre = doc.department %}
{% set mention_pied = "Vous recevez ce message car votre demande de congé a été traitée." %}

{% block titre %}Demande de congé approuvée{% endblock %}
{% block preheader %}Votre demande de congé a été approuvée.{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour " ~ doc.employee_name ~ ",") }}
{{ ui.p("Votre demande de congé a été approuvée.") }}
{{ ui.details([
  ("Période", "Du " ~ frappe.utils.formatdate(doc.from_date) ~ " au " ~ frappe.utils.formatdate(doc.to_date)),
  ("Nombre de jours", doc.total_leave_days),
  ("Type de congé", doc.leave_type),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Voir ma demande") }}
{% endblock %}
"""


def _message_hd_ticket():
	return ENTETE + """

{% set soustitre = doc.ticket_type %}
{% set mention_pied = "Ce ticket a été créé depuis le portail Helpdesk." %}

{% block titre %}Nouveau ticket Helpdesk{% endblock %}
{% block preheader %}Nouveau ticket : {{ doc.subject }}{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("Un nouveau ticket Helpdesk a été créé.") }}
{{ ui.details([
  ("Ticket", doc.name),
  ("Sujet", doc.subject),
  ("Priorité", doc.priority),
  ("Créé par", doc.raised_by),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Ouvrir le ticket") }}
{% endblock %}
"""


def _message_contact():
	return ENTETE + """

{% set soustitre = doc.entreprise %}
{% set mention_pied = "Ce message provient du formulaire de contact du site internet." %}

{% block titre %}Nouveau prospect{% endblock %}
{% block preheader %}Nouveau prospect : {{ doc.first_name }} {{ doc.last_name }}{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("Un nouveau prospect a rempli le formulaire de contact du site internet.") }}
{{ ui.details([
  ("Nom", (doc.first_name or "") ~ " " ~ (doc.last_name or "")),
  ("Société", doc.entreprise),
  ("Courriel", doc.email),
  ("Téléphone", doc.number),
  ("Service", doc.services),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Ouvrir le contact") }}
{% endblock %}
"""


def _message_candidat():
	return ENTETE + """

{% set soustitre = doc.job_title %}
{% set mention_pied = "Cette candidature a été reçue via le portail de recrutement." %}

{% block titre %}Nouveau candidat{% endblock %}
{% block preheader %}Nouveau candidat : {{ doc.applicant_name }}{% endblock %}

{% block contenu %}
{{ ui.p("Bonjour,") }}
{{ ui.p("Un nouveau candidat a été enregistré.") }}
{{ ui.details([
  ("Nom", doc.applicant_name),
  ("Courriel", doc.email_id),
  ("Poste", doc.job_title),
]) }}
{% endblock %}

{% block cta %}
{{ ui.bouton(frappe.utils.get_url_to_form(doc.doctype, doc.name), "Voir la candidature") }}
{% endblock %}
"""


# ---------------------------------------------------------------------------
# Diagnostic.
# ---------------------------------------------------------------------------
def etat():
	"""État des notifications : désactivées, remplacées, corrigées.

	    bench --site <site> execute amoamancustom.setup.notifications.etat
	"""
	print("== Notifications anglaises désactivées ==")
	for nom in NOTIFICATIONS_A_DESACTIVER:
		existe = frappe.db.exists("Notification", nom)
		if not existe:
			print(f"  ABSENT   {nom}")
			continue
		actif = frappe.db.get_value("Notification", nom, "enabled")
		print(f"  {'ACTIF' if actif else 'COUPÉ'}   {nom}")

	print("\n== Remplacements français ==")
	for notification in NOTIFICATIONS:
		nom = notification["nom"]
		existe = frappe.db.exists("Notification", nom)
		if not existe:
			print(f"  ABSENT   {nom}")
			continue
		actif = frappe.db.get_value("Notification", nom, "enabled")
		message = frappe.db.get_value("Notification", nom, "message") or ""
		etiquette = "HORS GABARIT" if GABARIT not in message else "OK"
		print(f"  {'ACTIF' if actif else 'COUPÉ'}   {nom}  [{etiquette}]")

	print("\n== Correctifs ==")
	for nom in (
		"Contrat proche expiration",
		"Demande de congés - en attente DG MAIL",
		"Demande de congés - en attente RH MAIL",
		"Validation Demande de congés",
		"New HD ticket",
		"Contact Notification",
		"Notifications candidat",
		"Inscription confirmée - Webinaire",
		"Alerte fin de contrat",
	):
		if not frappe.db.exists("Notification", nom):
			print(f"  ABSENT   {nom}")
			continue
		message = frappe.db.get_value("Notification", nom, "message") or ""
		canal = frappe.db.get_value("Notification", nom, "channel")
		if nom == "Inscription confirmée - Webinaire":
			# Son message n'utilise pas le gabarit (HTML dédié, déjà en français) :
			# le correctif porte sur le destinataire, pas sur le contenu.
			dest = frappe.get_all(
				"Notification Recipient",
				filters={"parent": nom, "parentfield": "recipients"},
				fields=["receiver_by_document_field"],
			)
			etiquette = (
				"OK" if any(d.receiver_by_document_field == "email" for d in dest) else "À CORRIGER"
			)
		elif nom in ("Contact Notification", "Notifications candidat", "New HD ticket"):
			etiquette = "OK" if (canal == "Email" and GABARIT in message) else "À CORRIGER"
		else:
			etiquette = "OK" if GABARIT in message else "HORS GABARIT"
		print(f"  {etiquette:<11} {nom}  [canal={canal}]")
