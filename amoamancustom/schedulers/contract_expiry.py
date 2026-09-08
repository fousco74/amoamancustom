# apps/amoamancustom/amoamancustom/schedulers/contract_expiry.py

import frappe
from frappe.utils import getdate, today, add_months


@frappe.whitelist()
def send_contract_expiry_notifications():
    """
    Envoie chaque jour un email récapitulatif aux RH (HR User + HR Manager)
    listant les employés actifs dont le contrat se termine dans le mois à venir.

    Source de vérité : le doctype `Contract` (CRM), avec `party_type == "Employee"`.
    C'est la même source que la notification « Contrat proche expiration » ; le
    champ standard `Employee.contract_end_date` est laissé vide (aucun employé ne
    le remplit), si bien que l'ancienne requête sur ce champ ne renvoyait jamais
    rien et le rappel ne partait jamais.

    Condition par contrat :
        - party_type == "Employee"
        - status == "Active"  (signé et en cours)
        - aujourd'hui <= end_date <= aujourd'hui + 1 mois

    Les envois s'arrêtent automatiquement au renouvellement (la date de fin est
    repoussée hors de la fenêtre) ou lorsque la date est dépassée.
    """

    start = getdate(today())
    end = add_months(start, 1)  # fenêtre = 1 mois à partir d'aujourd'hui

    contrats = frappe.get_all(
        "Contract",
        filters={
            "party_type": "Employee",
            "status": "Active",
            "end_date": ["between", [start, end]],
        },
        fields=["name", "party_name", "party_full_name", "end_date"],
        order_by="end_date asc",
    )

    # Rien à signaler -> pas d'email
    if not contrats:
        return

    recipients = get_hr_recipients()
    if not recipients:
        frappe.logger().warning(
            "Notification fin de contrat : aucun destinataire (HR User / HR Manager)."
        )
        return

    # Reconstruit la liste d'affichage attendue par le gabarit (name, employee_name,
    # department, designation, contract_end_date, days_left), en joignant la fiche
    # employé via `party_name` (identifiant de l'employé).
    employees = []
    for c in contrats:
        emp = frappe.db.get_value(
            "Employee",
            c.party_name,
            ["employee_name", "department", "designation"],
            as_dict=True,
        ) or {}
        employees.append(
            {
                "name": c.party_name,
                "employee_name": emp.get("employee_name") or c.party_full_name or c.party_name,
                "department": emp.get("department"),
                "designation": emp.get("designation"),
                "contract_end_date": c.end_date,
                "days_left": (getdate(c.end_date) - start).days,
            }
        )

    subject = f"Fin de contrat — {len(employees)} contrat(s) arrivant à échéance"
    # Le HTML vit dans amoamancustom/templates/emails/fin_de_contrat.html, qui
    # étend le gabarit commun _base_mail.html : mise en page, lien d'instance et
    # lien par employé sont partagés avec les autres mails de l'application.
    message = frappe.render_template(
        "amoamancustom/templates/emails/fin_de_contrat.html",
        {"employes": employees, "date_edition": start},
        is_path=True,
    )

    try:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
        )
    except Exception as e:
        frappe.log_error(
            title="Erreur envoi notification fin de contrat",
            message=str(e),
        )


def get_hr_recipients():
    """
    Retourne la liste (dédupliquée) des emails des utilisateurs ACTIFS ayant
    le rôle HR User ou HR Manager.
    """
    users = frappe.get_all(
        "Has Role",
        filters={
            "role": ["in", ["HR User", "HR Manager"]],
            "parenttype": "User",
        },
        distinct=True,
        pluck="parent",
    )

    if not users:
        return []

    # Exclure les comptes système non destinataires
    users = [u for u in users if u not in ("Administrator", "Guest")]
    if not users:
        return []

    emails = frappe.get_all(
        "User",
        filters={
            "name": ["in", users],
            "enabled": 1,
            "user_type": "System User",
        },
        pluck="email",
    )

    return list({e for e in emails if e})


