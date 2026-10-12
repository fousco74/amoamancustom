# apps/amoamancustom/amoamancustom/www/erpnext/mentions_legales.py
"""Mentions légales du mini-site ERPNext (/erpnext/mentions-legales).

Frappe cherche le contrôleur d'une page en remplaçant les tirets du nom de
fichier par des underscores (frappe/website/page_renderers/template_page.py:141) :
d'où mentions-legales.html + mentions_legales.py.

Le texte est celui de /legal-notice (templates/includes/legal/mentions_legales.html).
"""

from frappe import _

from amoamancustom.erpnext_site import base_context


def get_context(context):
	return base_context(
		context,
		title=_("Mentions légales"),
		description=_(
			"Éditeur, propriété intellectuelle et conditions d'accès du site ERPNext "
			"d'Amoaman & Associés."
		),
		page="legal",
	)
