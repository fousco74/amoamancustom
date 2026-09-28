# apps/amoamancustom/amoamancustom/www/erpnext/index.py
"""Accueil du mini-site « Amoaman intégrateur ERPNext » (/erpnext).

Le contenu est volontairement en dur : c'est de la page vitrine, elle ne bouge
qu'au rythme des refontes. Seule la tarification est éditable depuis le Desk
(cf. www/erpnext/tarification.py).
"""

import os

from frappe import _

from amoamancustom.erpnext_site import base_context, modules

# Photo de fond de la section « Pourquoi nous choisir » (calque Figma 4105:2900,
# « image 153 »). Elle n'a pas pu etre exportee avec le reste : tant que le
# fichier manque, la section s'affiche sur son degrade de repli et la page ne
# le reference pas — sans quoi chaque visite produirait un 404.
_FOND_POURQUOI = os.path.join(
	os.path.dirname(os.path.abspath(__file__)),
	"..", "..", "public", "images", "erpnext", "photo-bureau-fond.webp",
)


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
		page="accueil",
	)

	context.modules = modules()
	context.erpx_pq_fond = os.path.exists(_FOND_POURQUOI)
	return context
