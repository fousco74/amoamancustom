import frappe


def get_context(context):
	"""Calcule l'ancienneté pour le rappel d'anniversaire professionnel.

	Appelé par Notification.load_standard_properties avant le rendu. Sans cette
	injection, `annees` serait indéfini et rendrait une chaîne vide : le contexte
	d'une Notification ne contient que doc, nowdate, frappe, alert et comments.
	"""
	employe = context["doc"]

	annees = 0
	if employe.get("date_of_joining"):
		arrivee = frappe.utils.getdate(employe.date_of_joining)
		annees = frappe.utils.getdate().year - arrivee.year

	context["annees"] = annees
	return context
