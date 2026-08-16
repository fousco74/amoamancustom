# apps/amoamancustom/amoamancustom/schedulers/hr_reminders.py
"""
Rappels RH en français : anniversaire, anniversaire professionnel, jours fériés.

Remplacent les trois rappels de HRMS, dont le contenu est codé en dur dans
hrms/controllers/employee_reminders.py et qui n'exposent aucun champ
Email Template. Les quatre jobs correspondants de HRMS sont coupés par
amoamancustom/setup/scheduler.py (Scheduled Job Type.stopped), sans toucher au
code de l'app standard.

Deux opérations indépendantes : couper les jobs de HRMS fait taire l'anglais,
mais ne déclenche rien. Ce sont les entrées de `scheduler_events` dans hooks.py
qui font tourner ceux-ci.

Ces fonctions relisent les MÊMES cases de HR Settings que HRMS
(send_birthday_reminders, send_work_anniversary_reminders,
send_holiday_reminders, frequency) : l'écran de paramétrage RH garde donc
exactement le comportement qu'il avait auparavant.

Le contenu des mails n'est pas ici : il vit dans les Notification `is_standard`
de amoamancustom/hr_custom/notification/, modifiables sans toucher au code.
Ce module ne fait que sélectionner les employés et déclencher la notification
via `run_notifications`, l'API publique prévue pour l'événement « Method »
(frappe/model/document.py:1316).
"""

import frappe
from frappe.utils import add_days, add_months, getdate, today

from hrms.hr.utils import get_holidays_for_employee

# Correspondance méthode de notification -> champ date de l'employé.
# Ces valeurs sont interpolées dans du SQL : elles doivent rester des constantes
# de ce module, jamais une entrée utilisateur.
CHAMP_ANNIVERSAIRE = "date_of_birth"
CHAMP_ANCIENNETE = "date_of_joining"


def envoyer_rappels_anniversaire():
	"""Quotidien. Souhaite l'anniversaire des employés actifs nés un tel jour."""
	if not frappe.db.get_single_value("HR Settings", "send_birthday_reminders"):
		return

	_declencher_pour_employes(
		_employes_avec_evenement_aujourdhui(CHAMP_ANNIVERSAIRE),
		"rappel_anniversaire",
	)


def envoyer_rappels_anniversaire_pro():
	"""Quotidien. Célèbre l'ancienneté des employés entrés un tel jour."""
	if not frappe.db.get_single_value("HR Settings", "send_work_anniversary_reminders"):
		return

	_declencher_pour_employes(
		_employes_avec_evenement_aujourdhui(CHAMP_ANCIENNETE),
		"rappel_anniversaire_pro",
	)


def envoyer_rappels_feries_hebdo():
	"""Hebdomadaire. Ne fait rien si la cadence configurée est mensuelle."""
	_envoyer_rappels_feries("Weekly")


def envoyer_rappels_feries_mensuel():
	"""Mensuel. Ne fait rien si la cadence configurée est hebdomadaire."""
	_envoyer_rappels_feries("Monthly")


def _envoyer_rappels_feries(cadence_attendue: str):
	"""Annonce les jours fériés à venir, à chaque employé selon son calendrier.

	Deux jobs sont déclarés (hebdomadaire et mensuel) comme le fait HRMS, et
	chacun se retire si HR Settings.frequency ne le désigne pas. C'est ce qui
	permet à la cadence de rester pilotable depuis l'écran RH.
	"""
	if not frappe.db.get_single_value("HR Settings", "send_holiday_reminders"):
		return

	cadence = frappe.db.get_single_value("HR Settings", "frequency") or "Weekly"
	if cadence != cadence_attendue:
		return

	debut = getdate()
	fin = add_months(debut, 1) if cadence == "Monthly" else add_days(debut, 7)

	employes = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		pluck="name",
	)

	# On filtre ici plutôt que dans la notification : sans jour férié à annoncer,
	# le mail partirait avec un tableau vide.
	concernes = []
	for employe in employes:
		try:
			jours = get_holidays_for_employee(
				employe, debut, fin, only_non_weekly=True, raise_exception=False
			)
		except Exception:
			frappe.log_error(
				title="Rappel jours fériés : calendrier illisible",
				message=f"Employé {employe}\n\n{frappe.get_traceback()}",
			)
			continue

		if jours:
			concernes.append(employe)

	_declencher_pour_employes(concernes, "rappel_jours_feries")


def _employes_avec_evenement_aujourdhui(champ_date: str) -> list[str]:
	"""Identifiants des employés actifs dont `champ_date` tombe aujourd'hui.

	On n'utilise pas hrms.controllers.employee_reminders.get_employees_having_an_event_today :
	sa requête fait `employee_name AS 'name'`, si bien que la clé `name` qu'elle
	renvoie est le nom affiché et non l'identifiant — inexploitable pour
	frappe.get_doc.

	La comparaison porte sur le jour et le mois, l'année devant être antérieure :
	on ne souhaite pas l'anniversaire d'une naissance ou d'une embauche du jour.
	"""
	if champ_date not in (CHAMP_ANNIVERSAIRE, CHAMP_ANCIENNETE):
		frappe.throw(f"Champ de date non autorisé : {champ_date}")

	return frappe.db.sql_list(
		f"""
		SELECT name
		FROM `tabEmployee`
		WHERE status = 'Active'
		  AND {champ_date} IS NOT NULL
		  AND DAY({champ_date}) = DAY(%(jour)s)
		  AND MONTH({champ_date}) = MONTH(%(jour)s)
		  AND YEAR({champ_date}) < YEAR(%(jour)s)
		""",
		{"jour": today()},
	)


def _declencher_pour_employes(employes: list[str], methode: str):
	"""Déclenche la Notification « Method » portant `methode` pour chaque employé.

	Une erreur sur un employé ne doit pas interrompre les suivants : le job
	tourne sans surveillance, un enregistrement incomplet ne doit pas priver
	toute la société de son rappel.
	"""
	for employe in employes:
		try:
			frappe.get_doc("Employee", employe).run_notifications(methode)
		except Exception:
			frappe.log_error(
				title=f"Rappel RH en échec : {methode}",
				message=f"Employé {employe}\n\n{frappe.get_traceback()}",
			)
