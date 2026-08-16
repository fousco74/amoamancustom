import frappe

# Le gabarit HTML utilise des noms courts (secteur, besoin, m_compta…) alors que
# les données vivent dans les champs personnalisés du Lead, dont les noms sont
# générés à partir des libellés du formulaire web. Cette table fait le pont.
#
# Sans elle, ces variables sont simplement indéfinies : le contexte d'une
# Notification ne contient que doc, nowdate, frappe, alert et comments
# (frappe/email/doctype/notification/notification.py:840), et Jinja rend une
# chaîne vide pour tout le reste, sans lever d'erreur. C'est ce qui faisait
# partir des mails de prospect aux champs vides.
CHAMPS = {
	# Contact
	"first_name": "first_name",
	"last_name": "last_name",
	"job_title": "job_title",
	"email_id": "email_id",
	"whatsapp": "whatsapp_no",
	# Entreprise
	"company_name": "company_name",
	"no_of_employees": "no_of_employees",
	"secteur": "custom_secteur_dactivité",
	"activite_autres": "custom_activite_autres_",
	"besoin": "custom_décrivez_brièvement_votre_besoin_ou_vos_attentes",
	# Modules demandés
	"m_compta": "custom_comptabilité__finance",
	"m_immob": "custom_immobilisation",
	"m_achats": "custom_achats",
	"m_stocks": "custom_gestion_des_stocks",
	"m_ventes": "custom_ventes__crm",
	"m_pos": "custom_point_de_vente",
	"m_rh": "custom_ressources_humaines___paie",
	"m_prod": "custom_gestion_de_la_production",
	"m_qual": "custom_qualité",
	"m_projet": "custom_projet",
	"m_support": "custom_assistance_support",
	# Données à migrer
	"mig_clients": "custom_clients_",
	"mig_fournisseurs": "custom_fournisseurs",
	"mig_produits": "custom_produits_etou_services",
	"mig_factures": "custom_factures",
	"mig_stocks": "custom_stocks",
	"mig_salaries": "custom_salariés",
}


def get_context(context):
	"""Expose les champs du Lead sous les noms courts attendus par le gabarit."""
	lead = context["doc"]

	for alias, champ in CHAMPS.items():
		context[alias] = lead.get(champ)

	context["has_modules"] = any(context[a] for a in CHAMPS if a.startswith("m_"))
	context["has_migration"] = any(context[a] for a in CHAMPS if a.startswith("mig_"))

	return context
