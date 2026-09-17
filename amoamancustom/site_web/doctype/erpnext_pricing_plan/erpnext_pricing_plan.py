# Copyright (c) 2026, KONE Fousseni and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class ERPNextPricingPlan(Document):
	"""Offre tarifaire affichée sur /erpnext/tarification.

	L'ordre des cartes suit `idx` (glisser-déposer dans la liste du Desk), et
	non la date de création : c'est le seul critère que le marketing maîtrise
	sans développeur.
	"""

	pass
