# apps/amoamancustom/amoamancustom/schedulers/contract_expiry.py

import frappe
from frappe.utils import getdate, today, add_months


@frappe.whitelist()
def send_contract_expiry_notifications():
    """
    Envoie chaque jour un email récapitulatif aux RH (HR User + HR Manager)
    listant les employés actifs dont le contrat se termine dans le mois à venir.

    Condition par employé :
        - status == "Active"
        - aujourd'hui <= contract_end_date <= aujourd'hui + 1 mois

    Les envois s'arrêtent automatiquement au renouvellement (la date de fin est
    repoussée hors de la fenêtre) ou lorsque la date est dépassée.
    """

    start = getdate(today())
    end = add_months(start, 1)  # fenêtre = 1 mois à partir d'aujourd'hui

    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "contract_end_date": ["between", [start, end]],
        },
        fields=["name", "employee_name", "department", "designation", "contract_end_date"],
        order_by="contract_end_date asc",
    )

    # Rien à signaler -> pas d'email
    if not employees:
        return

    recipients = get_hr_recipients()
    if not recipients:
        frappe.logger().warning(
            "Notification fin de contrat : aucun destinataire (HR User / HR Manager)."
        )
        return

    # Nombre de jours restants par employé (date de fin précise conservée pour l'affichage)
    for emp in employees:
        emp["days_left"] = (getdate(emp["contract_end_date"]) - start).days

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


