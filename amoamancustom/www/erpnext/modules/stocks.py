# apps/amoamancustom/amoamancustom/www/erpnext/modules/stocks.py
"""Page module « Stocks » du mini-site ERPNext (/erpnext/modules/stocks).

Seule page module à ce stade. L'arborescence `modules/` et la liste canonique
`erpnext_site.MODULES` sont prêtes pour les onze autres : une page sœur se
crée en dupliquant ce fichier et en renseignant la `route` du module concerné.
"""

from frappe import _

from amoamancustom.erpnext_site import base_context, modules


def get_context(context):
	base_context(
		context,
		title=_("Gestion des stocks avec ERPNext"),
		description=_(
			"Visibilité en temps réel, contrôle multi-entrepôts, valorisation exacte : "
			"le module Stocks d'ERPNext implémenté par Amoaman & Associés."
		),
		active="modules",
	)

	# Le carrousel de bas de page propose les onze autres modules.
	context.autres_modules = modules(exclude="stocks")
	return context
