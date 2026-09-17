# apps/amoamancustom/amoamancustom/www/erpnext/tarification.py
"""Page tarifaire du mini-site ERPNext (/erpnext/tarification).

Seule page du mini-site dont le contenu vit en base : les offres sont des
documents `ERPNext Pricing Plan`, modifiables depuis le Desk sans passer par un
développeur. `setup/erpnext_pricing.py` les amorce à partir de la maquette.
"""

import frappe
from frappe import _

from amoamancustom.erpnext_site import base_context


def get_context(context):
	base_context(
		context,
		title=_("Tarification ERPNext"),
		description=_(
			"Trois formules ERPNext par Amoaman & Associés : Essentiel, Business et "
			"Entreprise. Nombre illimité d'utilisateurs, FNE intégrée, accompagnement "
			"et formation."
		),
		active="tarification",
	)

	# `get_all` ne ramène pas les tables enfants : on charge chaque document
	# pour disposer de ses `features`. Trois documents, l'écart est négligeable
	# et le template reste lisible.
	noms = frappe.get_all(
		"ERPNext Pricing Plan",
		filters={"published": 1},
		order_by="idx asc",
		pluck="name",
	)

	context.plans = [frappe.get_doc("ERPNext Pricing Plan", nom) for nom in noms]
	return context
