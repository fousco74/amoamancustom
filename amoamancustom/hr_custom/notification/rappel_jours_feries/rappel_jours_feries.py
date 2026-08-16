import frappe
from frappe.utils import add_days, add_months, getdate

from hrms.hr.utils import get_holidays_for_employee


def get_context(context):
	"""Charge les jours fériés à venir pour l'employé destinataire.

	Appelé par Notification.load_standard_properties avant le rendu. Le contexte
	d'origine ne contient que doc, nowdate, frappe, alert et comments : sans
	cette injection, `jours_feries`, `debut` et `fin` rendraient vide.

	La fenêtre suit HR Settings.frequency, comme le fait HRMS : une semaine en
	cadence hebdomadaire, un mois en cadence mensuelle.

	On réutilise get_holidays_for_employee plutôt que d'interroger la base :
	c'est ce helper qui résout le calendrier applicable (celui de l'employé, à
	défaut celui du service, à défaut celui de la société).
	"""
	employe = context["doc"]

	debut = getdate()
	cadence = frappe.db.get_single_value("HR Settings", "frequency") or "Weekly"
	fin = add_months(debut, 1) if cadence == "Monthly" else add_days(debut, 7)

	context["debut"] = debut
	context["fin"] = fin
	context["jours_feries"] = (
		get_holidays_for_employee(
			employe.name,
			debut,
			fin,
			only_non_weekly=True,
			raise_exception=False,
		)
		or []
	)

	return context
