# apps/amoamancustom/amoamancustom/schedulers/contract_expiry.py

import frappe
from frappe.utils import getdate, today, add_months, formatdate


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
    message = build_recap_html(employees, start)

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


def build_recap_html(employees, start):
    """
    Construit l'email HTML brandé « Amoaman & Associés » avec un tableau
    récapitulatif (une ligne par employé). Les fins de contrat sous 7 jours
    sont mises en évidence en rouge.
    """

    rows = ""
    for emp in employees:
        days_left = emp["days_left"]
        end_date = formatdate(emp["contract_end_date"])

        if days_left <= 0:
            delay_label = "Aujourd'hui"
        elif days_left == 1:
            delay_label = "Demain"
        else:
            delay_label = f"Dans {days_left} jour(s)"

        urgent = days_left <= 7
        date_style = "font-weight: 600; color: #c0392b;" if urgent else "font-weight: 600; color: #333;"
        delay_style = "font-weight: 600; color: #c0392b;" if urgent else "color: #333;"

        rows += f"""
            <tr style="border-bottom: 1px solid #e0e0e0;">
                <td style="padding: 10px 12px; font-size: 14px; color: #333;">{emp.get('employee_name') or emp.get('name')}</td>
                <td style="padding: 10px 12px; font-size: 14px; color: #555;">{emp.get('department') or '—'}</td>
                <td style="padding: 10px 12px; font-size: 14px; color: #555;">{emp.get('designation') or '—'}</td>
                <td style="padding: 10px 12px; font-size: 14px; {date_style}">{end_date}</td>
                <td style="padding: 10px 12px; font-size: 14px; {delay_style}">{delay_label}</td>
            </tr>
        """

    count = len(employees)
    generated_on = formatdate(start)

    message = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 680px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden;">

        <div style="background-color: #1a3c5e; padding: 24px 32px;">
            <p style="margin: 0; color: #ffffff; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; font-weight: 600;">Amoaman &amp; Associés — Ressources Humaines</p>
        </div>

        <div style="padding: 32px;">
            <h2 style="margin: 0 0 8px 0; color: #1a3c5e; font-size: 20px; font-weight: 700;">Contrats arrivant à échéance</h2>
            <p style="margin: 0 0 24px 0; color: #777; font-size: 13px; border-bottom: 1px solid #e0e0e0; padding-bottom: 16px;">État au {generated_on} — {count} contrat(s) se terminant dans le mois à venir</p>

            <p style="color: #333; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Les contrats des employés ci-dessous arrivent à échéance dans moins d'un mois.
                Merci d'anticiper leur <strong>renouvellement</strong> ou les démarches de fin de contrat.
                Ce rappel est envoyé chaque jour tant que la date de fin n'est pas repoussée.
            </p>

            <table style="width: 100%; border-collapse: collapse; margin: 0 0 24px 0;">
                <thead>
                    <tr style="background-color: #f5f7fa; border-bottom: 2px solid #1a3c5e;">
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #1a3c5e;">Employé</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #1a3c5e;">Département</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #1a3c5e;">Poste</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #1a3c5e;">Date de fin</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #1a3c5e;">Échéance</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>

            <p style="color: #555; font-size: 14px; line-height: 1.6; margin: 0;">
                Pour toute question, veuillez contacter le département Ressources Humaines.
            </p>
        </div>

        <div style="background-color: #f5f7fa; padding: 16px 32px; border-top: 1px solid #e0e0e0;">
            <p style="margin: 0; color: #999; font-size: 12px;">Ce message est généré automatiquement par le système ERPNext — Amoaman &amp; Associés. Merci de ne pas y répondre directement.</p>
        </div>
    </div>
    """

    return message
