# apps/amoamancustom/amoamancustom/setup/payroll.py
"""
Amorce le drapeau « Print on Salary Slip » sur les composantes déjà imprimées.

Le bulletin « Slip de Salaire » listait ses rubriques en dur (un bloc <tr> par
composante, codes 00.1, 00.2, 00.5, 00.6, 500, 530, 787, 840). Il boucle
désormais sur les lignes du bulletin en ne retenant que celles dont la Salary
Component porte `custom_print_on_salary_slip`.

Ce champ naît à 0 : sans amorçage, le premier bulletin imprimé après la
migration sortirait vide. On pose donc le drapeau sur les rubriques que
l'ancien gabarit imprimait explicitement. Les indemnités du solde de tout
compte arrivent déjà avec le drapeau, via fixtures/salary_component.json.

Pourquoi `after_migrate` et pas un patch : les patches `post_model_sync`
tournent AVANT `Syncing fixtures...` (frappe/migrate.py), donc avant que le
Custom Field n'existe. Un patch aurait trouvé la colonne absente, serait sorti
sans rien faire, et aurait été enregistré comme joué — donc jamais rejoué.
`after_migrate` tourne en fin de migration, une fois les fixtures importées.

Idempotent : on n'écrit que si la valeur n'est pas déjà à 1, et une composante
absente du site est simplement signalée.

    bench --site <site> execute amoamancustom.setup.payroll.etat
        rapport sans écriture (ACTIF / INACTIF / ABSENT)
"""

import frappe

# Rubriques présentes dans l'ancien gabarit slip_de_salaire.html.
COMPOSANTES_IMPRIMEES = (
	"Salaire de base",
	"Sursalaire",
	"Indemnité de Congés",
	"Gratification",
	"Retenue ITS",
	"Retenue CNPS",
	"Prime de Transport",
	"Retenue CMU",
)

CHAMP = "custom_print_on_salary_slip"


def installer():
	"""Point d'entrée appelé par `after_migrate`. Idempotent."""
	if not frappe.db.has_column("Salary Component", CHAMP):
		frappe.log_error(
			message=(
				f"Colonne {CHAMP} absente de Salary Component : le drapeau d'impression "
				"n'a pas pu être amorcé. Relancer `bench migrate` puis "
				"`bench execute amoamancustom.setup.payroll.installer`."
			),
			title="STC_PRINT_FLAG_CHAMP_ABSENT",
		)
		return

	poses, absentes = [], []

	for nom in COMPOSANTES_IMPRIMEES:
		if not frappe.db.exists("Salary Component", nom):
			absentes.append(nom)
			continue
		if frappe.db.get_value("Salary Component", nom, CHAMP):
			continue
		frappe.db.set_value("Salary Component", nom, CHAMP, 1, update_modified=False)
		poses.append(nom)

	if poses:
		print("Impression bulletin activée sur : %s" % ", ".join(poses))

	if absentes:
		frappe.log_error(
			message=(
				"Composantes salariales absentes, drapeau %s non posé : %s.\n"
				"Vérifier qu'elles apparaissent bien sur le bulletin imprimé." % (CHAMP, ", ".join(absentes))
			),
			title="STC_PRINT_FLAG_COMPOSANTE_ABSENTE",
		)

	frappe.db.commit()


def etat():
	"""Rapport lisible, sans écriture."""
	if not frappe.db.has_column("Salary Component", CHAMP):
		print("Colonne %s absente : lancer `bench migrate` d'abord." % CHAMP)
		return

	for nom in COMPOSANTES_IMPRIMEES:
		if not frappe.db.exists("Salary Component", nom):
			print("ABSENT   %s" % nom)
		elif frappe.db.get_value("Salary Component", nom, CHAMP):
			print("ACTIF    %s" % nom)
		else:
			print("INACTIF  %s" % nom)

	autres = frappe.get_all(
		"Salary Component",
		filters={CHAMP: 1, "name": ("not in", COMPOSANTES_IMPRIMEES)},
		pluck="name",
	)
	if autres:
		print("\nAutres composantes imprimées : %s" % ", ".join(autres))
