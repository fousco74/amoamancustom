# apps/amoamancustom/amoamancustom/www/erpnext/cookies.py
"""Gestion des cookies du mini-site ERPNext (/erpnext/cookies).

Le texte et la carte de préférences sont ceux de /cookies, partagés via
templates/includes/legal/ : seul l'habillage change. Les préférences pilotent
la même clé `cookie_prefs_v1` que le site corporate (public/js/cookie_consent.js).
"""

from frappe import _

from amoamancustom.erpnext_site import base_context


def get_context(context):
	return base_context(
		context,
		title=_("Gestion des cookies"),
		description=_(
			"Cookies utilisés sur le site ERPNext d'Amoaman & Associés et réglage de vos "
			"préférences de confidentialité."
		),
		page="legal",
	)
