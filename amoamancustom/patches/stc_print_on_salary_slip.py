"""Amorce custom_print_on_salary_slip sur les composantes deja imprimees.

Le bulletin « Slip de Salaire » listait ses rubriques en dur (un bloc <tr> par
composante). Il boucle desormais sur les lignes du bulletin en ne retenant que
celles dont la Salary Component porte custom_print_on_salary_slip.

Ce champ nait a 0 : sans amorcage, le premier bulletin imprime apres la
migration sortirait vide. On pose donc le drapeau sur les composantes qui
figuraient explicitement dans l'ancien gabarit. Les indemnites du solde de tout
compte arrivent deja avec le drapeau via fixtures/salary_component.json.

Idempotent : on n'ecrit que si la valeur n'est pas deja a 1, et une composante
absente du site est simplement ignoree.
"""

import frappe

# Rubriques presentes dans l'ancien gabarit slip_de_salaire.html
# (codes 00.1, 00.2, 00.5, 00.6, 500, 530, 787, 840).
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


def execute():
    if not frappe.db.has_column("Salary Component", CHAMP):
        # Le champ custom n'est pas encore materialise : rien a amorcer.
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
        print("Impression bulletin activee sur : %s" % ", ".join(poses))
    if absentes:
        frappe.log_error(
            message=(
                "Composantes salariales absentes, drapeau %s non pose : %s.\n"
                "Verifier qu'elles apparaissent bien sur le bulletin imprime."
                % (CHAMP, ", ".join(absentes))
            ),
            title="STC_PRINT_FLAG_COMPOSANTE_ABSENTE",
        )

    frappe.db.commit()
