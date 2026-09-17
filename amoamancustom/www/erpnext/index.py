# apps/amoamancustom/amoamancustom/www/erpnext/index.py
"""Accueil du mini-site « Amoaman intégrateur ERPNext » (/erpnext).

Le contenu est volontairement en dur : c'est de la page vitrine, elle ne bouge
qu'au rythme des refontes. Seule la tarification est éditable depuis le Desk
(cf. www/erpnext/tarification.py).
"""

from frappe import _

from amoamancustom.erpnext_site import base_context, modules


def get_context(context):
	base_context(
		context,
		title=_("ERPNext par Amoaman & Associés"),
		description=_(
			"Amoaman & Associés implémente ERPNext en Côte d'Ivoire et au Sénégal : "
			"comptabilité avec intégration FNE, RH, stocks, ventes, production. "
			"Une plateforme unique pour piloter toute votre activité."
		),
		active="",
	)

	context.modules = modules()
	return context
