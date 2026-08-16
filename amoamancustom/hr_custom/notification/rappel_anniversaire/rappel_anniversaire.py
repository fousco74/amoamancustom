import frappe


def get_context(context):
	"""Enrichit le contexte du rappel d'anniversaire.

	Appelé par Notification.load_standard_properties avant le rendu, pour les
	notifications marquées `is_standard`. Le contexte fourni d'origine ne
	contient que doc, nowdate, frappe, alert et comments : tout le reste doit
	être injecté ici.
	"""
	employe = context["doc"]

	context["age"] = None
	if employe.get("date_of_birth"):
		naissance = frappe.utils.getdate(employe.date_of_birth)
		aujourdhui = frappe.utils.getdate()
		context["age"] = aujourdhui.year - naissance.year

	return context
