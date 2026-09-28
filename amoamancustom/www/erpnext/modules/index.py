# apps/amoamancustom/amoamancustom/www/erpnext/modules/index.py
"""Catalogue des modules du mini-site ERPNext (/erpnext/modules).

Frappe rend `index.html` d'un dossier de www/ a la route du dossier : ce fichier
sert donc /erpnext/modules, et stocks.py sert /erpnext/modules/stocks, sans regle
supplementaire dans website_route_rules.

La page est la destination de repli de tous les modules sans page dediee
(erpnext_site.PAGE_MODULES). Avant qu'elle n'existe, les tuiles de l'accueil et
les liens du footer pointaient sur /erpnext#modules, c'est-a-dire sur la section
qu'on venait de cliquer.

Le contenu des cartes (intitules, descriptions, glyphes) vit dans
erpnext_site.MODULES, partage avec la grille de tuiles de l'accueil et le
carrousel des pages module.
"""

from frappe import _

from amoamancustom.erpnext_site import base_context, modules_detailles


def get_context(context):
	base_context(
		context,
		title=_("Les modules ERPNext par Amoaman & Associés"),
		description=_(
			"Comptabilité et intégration FNE, achats, production, projets, ventes, CRM, "
			"stocks, qualité, immobilisations, RH & paie, support, points de vente : "
			"les douze modules ERPNext implémentés par Amoaman & Associés."
		),
		active="modules",
		page="modules",
	)

	context.modules_cartes = modules_detailles()
	return context
