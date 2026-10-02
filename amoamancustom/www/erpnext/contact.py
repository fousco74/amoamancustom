# apps/amoamancustom/amoamancustom/www/erpnext/contact.py
"""Formulaire de contact du mini-site ERPNext (/erpnext/contact), qui crée un Lead.

Les listes déroulantes sont lues depuis `amoamancustom.contact_api` : c'est le
même module qui les contraint côté serveur. Les dupliquer dans le template
aurait garanti qu'elles divergent à la première retouche, et donc des rejets
incompréhensibles pour le visiteur.
"""

from frappe import _

from amoamancustom.contact_api import MODULES, PAYS_DEFAUT, TAILLES, indicatifs, secteurs
from amoamancustom.erpnext_site import base_context


def get_context(context):
	base_context(
		context,
		title=_("Contactez-nous"),
		description=_(
			"Parlons de votre projet ERPNext. Amoaman & Associés vous accompagne de "
			"l'analyse au déploiement, à Abidjan et à Dakar."
		),
		active="contact",
		page="contact",
	)

	context.tailles = TAILLES
	context.secteurs = secteurs()
	context.modules_liste = list(MODULES)
	context.indicatifs = indicatifs()
	context.pays_defaut = PAYS_DEFAUT
	return context
