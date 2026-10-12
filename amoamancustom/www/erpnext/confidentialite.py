# apps/amoamancustom/amoamancustom/www/erpnext/confidentialite.py
"""Politique de confidentialité du mini-site ERPNext (/erpnext/confidentialite).

Le texte et le sommaire sont ceux de /confidentialite
(templates/includes/legal/confidentialite*.html).
"""

from frappe import _

from amoamancustom.erpnext_site import base_context


def get_context(context):
	return base_context(
		context,
		title=_("Politique de confidentialité"),
		description=_(
			"Comment Amoaman & Associés traite vos données à caractère personnel et comment "
			"exercer vos droits."
		),
		page="legal",
	)
