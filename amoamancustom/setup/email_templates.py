# apps/amoamancustom/amoamancustom/setup/email_templates.py
"""
Pose les Email Template français d'Amoaman & Associés et les branche
dans les paramètres qui les consomment.

Reprend le mécanisme employé par HRMS pour ses propres modèles
(hrms/setup.py:429) : le HTML vit dans des fichiers versionnés de l'app, et un
installeur idempotent crée l'enregistrement s'il est absent. Un modèle déjà
présent n'est jamais réécrit — les retouches faites dans l'interface survivent
donc à `bench migrate`.

Le fichier est la référence d'installation, la base est la vérité d'exécution.
Deux commandes encadrent le cycle :

    bench --site <site> execute amoamancustom.setup.email_templates.reinitialiser
        force fichier -> base (repart de la version de référence)

    bench --site <site> execute amoamancustom.setup.email_templates.exporter
        force base -> fichier (capture dans git les retouches validées)

Aucune app standard n'est modifiée : on ne fait qu'écrire des enregistrements
et renseigner des champs de paramétrage.
"""

import os

import frappe

DOSSIER_MODELES = ("amoamancustom", "templates", "emails")

# `use_html` n'est PAS un choix esthétique.
#
#   use_html = 1 -> le contenu est stocké dans `response_html` (champ Code, non
#                   nettoyé). Réservé aux mails dont l'appelant lit `response_`.
#   use_html = 0 -> le contenu est stocké dans `response` (champ Text Editor,
#                   passé à sanitize_html). OBLIGATOIRE pour les cinq appelants
#                   qui lisent `.response` en dur et ignorent `response_html` :
#                   cocher « Ajouter du HTML » y viderait purement le mail.
#
# `sujet_jinja` indique si l'appelant passe le sujet à Jinja. Quand il vaut
# False, le sujet doit rester du texte brut : une expression y ressortirait
# telle quelle dans la boîte de réception.
MODELES = [
	{
		"nom": "Email de Bienvenue",
		"fichier": "bienvenue.html",
		"sujet": "Bienvenue chez Amoaman & Associés",
		"use_html": 1,
		"sujet_jinja": True,
		"reglage": ("System Settings", "welcome_email_template"),
	},
	{
		"nom": "Réinitialisation de mot de passe",
		"ancien_nom": "Modèle Réinitialisation de mot de passe",
		"fichier": "reinitialisation_mot_de_passe.html",
		"sujet": "Réinitialisation de votre mot de passe",
		"use_html": 1,
		"sujet_jinja": True,
		"reglage": ("System Settings", "reset_password_template"),
	},
	{
		"nom": "Notification d'approbation de congé",
		"ancien_nom": "Leave Approval Notification",
		"fichier": "conge_approbation.html",
		"sujet": "Demande de congé à valider — {{ employee_name }}",
		"use_html": 1,
		"sujet_jinja": True,
		"reglage": ("HR Settings", "leave_approval_notification_template"),
	},
	{
		"nom": "Notification de statut de congé",
		"ancien_nom": "Leave Status Notification",
		"fichier": "conge_statut.html",
		"sujet": "Suite donnée à votre demande de congé du {{ frappe.utils.formatdate(from_date, 'dd/MM/yyyy') }}",
		"use_html": 1,
		"sujet_jinja": True,
		"reglage": ("HR Settings", "leave_status_notification_template"),
	},
	{
		"nom": "Rappel d'entretien",
		"ancien_nom": "Interview Reminder",
		"fichier": "rappel_entretien.html",
		"sujet": "Rappel : entretien à venir",
		"use_html": 0,
		"sujet_jinja": False,
		"reglage": ("HR Settings", "interview_reminder_template"),
	},
	{
		"nom": "Rappel de retour d'entretien",
		"ancien_nom": "Interview Feedback Reminder",
		"fichier": "rappel_feedback_entretien.html",
		"sujet": "Votre évaluation d'entretien est attendue",
		"use_html": 0,
		"sujet_jinja": False,
		"reglage": ("HR Settings", "feedback_reminder_notification_template"),
	},
	{
		"nom": "Questionnaire de départ",
		"ancien_nom": "Exit Questionnaire Notification",
		"fichier": "questionnaire_de_depart.html",
		"sujet": "Votre avis sur votre expérience chez Amoaman & Associés",
		"use_html": 0,
		"sujet_jinja": False,
		"reglage": ("HR Settings", "exit_questionnaire_notification_template"),
	},
	{
		"nom": "Notification d'expédition",
		"fichier": "notification_expedition.html",
		"sujet": "Votre commande est en route",
		"use_html": 0,
		"sujet_jinja": False,
		"reglage": ("Delivery Settings", "dispatch_template"),
	},
	{
		"nom": "Bulletin de paie",
		"fichier": "bulletin_de_paie.html",
		"sujet": "Votre bulletin de paie — {{ frappe.utils.formatdate(start_date, 'MMMM yyyy') }}",
		"use_html": 0,
		"sujet_jinja": True,
		"reglage": ("Payroll Settings", "email_template"),
	},
]


def chemin_modele(fichier: str) -> str:
	return os.path.join(frappe.get_app_path(*DOSSIER_MODELES), fichier)


def lire_modele(fichier: str) -> str:
	with open(chemin_modele(fichier), encoding="utf-8") as f:
		return f.read()


def installer():
	"""Point d'entrée appelé par `after_migrate`. Idempotent."""
	renommer_modeles_anglais()

	for modele in MODELES:
		creer_si_absent(modele)
		brancher_reglage(modele)


def renommer_modeles_anglais():
	"""Passe en français les modèles livrés en anglais par HRMS.

	`rename_doc` répercute le nouveau nom dans tous les champs Link qui pointent
	dessus, y compris ceux des doctypes Single (frappe/model/rename_doc.py:417) :
	les branchements de HR Settings et consorts suivent donc automatiquement.
	"""
	for modele in MODELES:
		ancien = modele.get("ancien_nom")
		nouveau = modele["nom"]

		if not ancien or ancien == nouveau:
			continue
		if not frappe.db.exists("Email Template", ancien):
			continue
		if frappe.db.exists("Email Template", nouveau):
			# Les deux coexistent : le renommage a déjà eu lieu et quelqu'un a
			# recréé l'ancien. On ne tranche pas à sa place.
			frappe.log_error(
				title="Modèles de courriel : doublon",
				message=f"« {ancien} » et « {nouveau} » coexistent. "
				"Vérifier lequel est branché dans les paramètres, puis supprimer l'autre.",
			)
			continue

		# L'alias frappe.rename_doc n'accepte pas ignore_permissions, contrairement
		# à frappe.model.rename_doc.rename_doc. Inutile ici : after_migrate
		# s'exécute en tant qu'Administrator.
		frappe.rename_doc(
			"Email Template",
			ancien,
			nouveau,
			force=True,
			show_alert=False,
		)


def creer_si_absent(modele: dict) -> bool:
	"""Crée le modèle s'il n'existe pas. Ne touche jamais à un modèle existant."""
	if frappe.db.exists("Email Template", modele["nom"]):
		return False

	doc = frappe.new_doc("Email Template")
	doc.name = modele["nom"]
	appliquer_contenu(doc, modele)
	doc.insert(ignore_permissions=True)
	return True


def appliquer_contenu(doc, modele: dict):
	contenu = lire_modele(modele["fichier"])
	doc.subject = modele["sujet"]
	doc.use_html = modele["use_html"]

	if modele["use_html"]:
		doc.response_html = contenu
	else:
		doc.response = contenu


def brancher_reglage(modele: dict) -> bool:
	"""Renseigne le champ de paramétrage s'il est vide.

	On ne réécrit pas un champ déjà renseigné : si quelqu'un a délibérément
	pointé vers un autre modèle, c'est son choix.
	"""
	doctype, champ = modele["reglage"]

	if not frappe.db.exists("DocType", doctype):
		# L'app qui fournit ce réglage n'est pas installée sur ce site.
		return False

	if frappe.db.get_single_value(doctype, champ):
		return False

	frappe.db.set_single_value(doctype, champ, modele["nom"])
	return True


def reinitialiser(nom: str | None = None):
	"""Force fichier -> base. Écrase le contenu, y compris les retouches UI.

	    bench --site <site> execute amoamancustom.setup.email_templates.reinitialiser
	    bench --site <site> execute amoamancustom.setup.email_templates.reinitialiser --kwargs '{"nom": "Bulletin de paie"}'
	"""
	for modele in MODELES:
		if nom and modele["nom"] != nom:
			continue
		if not frappe.db.exists("Email Template", modele["nom"]):
			creer_si_absent(modele)
			print(f"créé      {modele['nom']}")
			continue

		doc = frappe.get_doc("Email Template", modele["nom"])
		appliquer_contenu(doc, modele)
		doc.save(ignore_permissions=True)
		print(f"réécrit   {modele['nom']}")

	frappe.db.commit()


def etat():
	"""Compare le contenu en base au fichier de référence, sans rien modifier.

	    bench --site <site> execute amoamancustom.setup.email_templates.etat

	Utile en reprise : `installer` ne réécrit jamais un modèle existant, si bien
	qu'un modèle déjà livré par HRMS garde son contenu d'origine. Cette commande
	dit lesquels sont à passer par `reinitialiser`, et lesquels ont été retouchés
	dans l'interface et méritent un `exporter` avant d'être propagés.
	"""
	for modele in MODELES:
		nom = modele["nom"]

		if not frappe.db.exists("Email Template", nom):
			print(f"ABSENT      {nom}")
			continue

		doc = frappe.get_doc("Email Template", nom)
		en_base = (doc.response_html if doc.use_html else doc.response) or ""
		fichier = lire_modele(modele["fichier"])

		if en_base.strip() == fichier.strip():
			etiquette = "IDENTIQUE  "
		elif "_base_mail.html" not in en_base:
			etiquette = "HORS GABARIT"
		else:
			etiquette = "DIVERGENT  "

		print(f"{etiquette} {nom}")

		doctype, champ = modele["reglage"]
		if frappe.db.exists("DocType", doctype):
			branche = frappe.db.get_single_value(doctype, champ)
			if branche != nom:
				print(f"             {doctype}.{champ} pointe sur {branche!r}")


def exporter(nom: str | None = None):
	"""Force base -> fichier. Capture dans git les retouches faites dans l'UI.

	    bench --site <site> execute amoamancustom.setup.email_templates.exporter

	Le sujet n'est pas exporté : il vit dans MODELES, à mettre à jour à la main
	si le client l'a modifié (la commande le signale).
	"""
	for modele in MODELES:
		if nom and modele["nom"] != nom:
			continue
		if not frappe.db.exists("Email Template", modele["nom"]):
			print(f"absent    {modele['nom']}")
			continue

		doc = frappe.get_doc("Email Template", modele["nom"])
		contenu = doc.response_html if doc.use_html else doc.response

		if not contenu:
			print(f"vide      {modele['nom']} — rien à exporter")
			continue

		with open(chemin_modele(modele["fichier"]), "w", encoding="utf-8") as f:
			f.write(contenu)
		print(f"exporté   {modele['nom']} -> {modele['fichier']}")

		if doc.subject != modele["sujet"]:
			print(f"          sujet modifié dans l'UI : {doc.subject!r} — reporter dans MODELES")
		if int(doc.use_html or 0) != modele["use_html"]:
			print(f"          ATTENTION use_html vaut {doc.use_html}, attendu {modele['use_html']}")
