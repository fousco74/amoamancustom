# apps/your_app/your_app/customizations/attendance_reminder.py

from frappe.utils import getdate, today, get_first_day, get_last_day
from datetime import datetime, timedelta
import frappe

@frappe.whitelist()
def send_attendance_reminder_continuous():
    """
    Envoie des rappels CONTINUS jusqu'à saisie de présence
    - 20-24 du mois: Rappels quotidiens
    - Après 24: Rappels tous les 2 jours jusqu'à saisie
    - Arrêt automatique une fois saisi
    """
    
    current_day = getdate(today()).day
    current_month = getdate(today()).month
    current_year = getdate(today()).year
    
    # Récupérer tous les employés actifs
    employees = frappe.get_list(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "user_id", "department"]
    )
    
    for emp in employees:
        # Vérifier si l'employé a saisi sa présence CE MOIS-CI
        has_checkin = check_employee_has_attendance(
            emp["name"], 
            current_year, 
            current_month
        )
        
        # ✅ Si DÉJÀ saisi = Ne pas envoyer de rappel
        if has_checkin:
            continue
        
        # ❌ Si PAS saisi = Décider du type de rappel
        reminder_type = get_reminder_type(current_day)
        
        if reminder_type:
            employee_email = emp.get("user_id")
            if not employee_email:
                continue
            should_send = check_send_conditions(employee_email, emp["name"], current_day, reminder_type)

            if should_send:
                send_reminder_email(emp, reminder_type, current_day)


def check_employee_has_attendance(employee_id, year, month):
    """
    Vérifie si l'employé a DÉJÀ saisi sa présence ce mois-ci
    Retourne: True/False
    """
    first_day = getdate(f"{year}-{month:02d}-01")
    last_day = get_last_day(first_day)
    
    count = frappe.db.count(
        "Attendance",
        filters={
            "employee": employee_id,
            "docstatus": 1,  # Validé
            "attendance_date": ["between", [first_day, last_day]]
        }
    )
    
    return count > 0


def get_reminder_type(current_day):
    """
    Détermine le type de rappel selon le jour du mois
    
    Stratégie:
    - Jour 20-24: Rappel quotidien (URGENT)
    - Jour 25+: Rappel tous les 2 jours (RELANCE)
    - Jour 1-19: Pas de rappel (Trop tôt)
    """
    
    if current_day >= 20 and current_day <= 24:
        return "daily"      # Rappel quotidien
    elif current_day >= 25:
        return "every_2_days"  # Rappel tous les 2 jours
    else:
        return None         # Pas de rappel




def check_send_conditions(employee_email, employee_name, current_day, reminder_type):
    """
    Vérifie si on doit envoyer le rappel aujourd'hui.
    Utilise reference_doctype/reference_name pour identifier les emails envoyés
    car tabEmail Queue ne stocke pas le sujet ni les destinataires directement
    (les destinataires sont dans tabEmail Queue Recipient, champ `recipient`).
    """

    if reminder_type == "daily":
        return True

    elif reminder_type == "every_2_days":

        # Vérifier si un email a déjà été envoyé aujourd'hui pour cet employé
        email_sent_today = frappe.db.sql("""
            SELECT eq.name
            FROM `tabEmail Queue` eq
            INNER JOIN `tabEmail Queue Recipient` eqr ON eqr.parent = eq.name
            WHERE eqr.recipient = %(email)s
              AND eq.reference_doctype = 'Employee'
              AND eq.reference_name = %(employee_name)s
              AND eq.status = 'Sent'
              AND DATE(eq.creation) = CURDATE()
            LIMIT 1
        """, {"email": employee_email, "employee_name": employee_name})

        if email_sent_today:
            return False

        # Récupérer la date du dernier email envoyé
        last_email = frappe.db.sql("""
            SELECT eq.creation
            FROM `tabEmail Queue` eq
            INNER JOIN `tabEmail Queue Recipient` eqr ON eqr.parent = eq.name
            WHERE eqr.recipient = %(email)s
              AND eq.reference_doctype = 'Employee'
              AND eq.reference_name = %(employee_name)s
              AND eq.status = 'Sent'
            ORDER BY eq.creation DESC
            LIMIT 1
        """, {"email": employee_email, "employee_name": employee_name}, as_dict=True)

        if last_email:
            last_date = getdate(last_email[0]["creation"])
            days_since = (getdate(today()) - last_date).days
            return days_since >= 2

        return True

    return False

def send_reminder_email(employee, reminder_type, current_day):
    """
    Envoie l'email de rappel avec le contenu approprié
    """

    user_id = employee.get("user_id")

    if not user_id:
        frappe.logger().warning(
            f"Employee {employee.get('name')} has no linked user_id"
        )
        return

    user = frappe.get_doc("User", user_id)
        
    if not user.email:
        return
    
    # Déterminer le sujet et le message selon le type
    if reminder_type == "daily" and current_day <= 24:
        subject, message = get_urgent_reminder(employee, current_day)
    else:
        subject, message = get_relance_reminder(employee, current_day)
    
    try:
        frappe.sendmail(
            recipients=[user.email],
            subject=subject,
            message=message,
            reference_doctype="Employee",
            reference_name=employee.get("name")
        )
        
        # Logging
        log_reminder_sent(employee.get("name"), subject, user.email)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(
            title=f"Erreur envoi rappel présence {employee.get('name')}",
            message=str(e)
        )


def get_urgent_reminder(employee, current_day):
    emp_name = employee.get("employee_name")
    days_remaining = 24 - current_day

    subject = f"Rappel : Saisie de présence requise — échéance dans {days_remaining} jour(s)"

    message = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden;">

        <div style="background-color: #1a3c5e; padding: 24px 32px;">
            <p style="margin: 0; color: #ffffff; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; font-weight: 600;">Amoaman &amp; Associés — Ressources Humaines</p>
        </div>

        <div style="padding: 32px;">
            <h2 style="margin: 0 0 8px 0; color: #1a3c5e; font-size: 20px; font-weight: 700;">Rappel de saisie de présence</h2>
            <p style="margin: 0 0 24px 0; color: #777; font-size: 13px; border-bottom: 1px solid #e0e0e0; padding-bottom: 16px;">Échéance : le 24 du mois en cours</p>

            <p style="color: #333; font-size: 15px; margin: 0 0 16px 0;">Madame, Monsieur <strong>{emp_name}</strong>,</p>

            <p style="color: #333; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Nous vous informons que votre feuille de présence du mois en cours n'a pas encore été enregistrée dans le système.
                Il vous reste <strong style="color: #c0392b;">{days_remaining} jour(s)</strong> pour effectuer cette saisie avant la date limite du <strong>24 du mois</strong>.
            </p>

            <div style="background-color: #f5f7fa; border-left: 4px solid #1a3c5e; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 0 4px 4px 0;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #333;">
                    <tr><td style="padding: 6px 0; color: #777; width: 160px;">Statut</td><td style="padding: 6px 0; font-weight: 600; color: #c0392b;">Non saisi</td></tr>
                    <tr><td style="padding: 6px 0; color: #777;">Date actuelle</td><td style="padding: 6px 0; font-weight: 600;">{current_day} du mois</td></tr>
                    <tr><td style="padding: 6px 0; color: #777;">Date limite</td><td style="padding: 6px 0; font-weight: 600;">24 du mois</td></tr>
                    <tr><td style="padding: 6px 0; color: #777;">Jours restants</td><td style="padding: 6px 0; font-weight: 600; color: #c0392b;">{days_remaining} jour(s)</td></tr>
                </table>
            </div>

            <p style="color: #333; font-size: 14px; font-weight: 600; margin: 0 0 10px 0;">Procédure de saisie :</p>
            <ol style="color: #333; font-size: 14px; line-height: 1.8; margin: 0 0 24px 0; padding-left: 20px;">
                <li>Connectez-vous à <strong>ERPNext</strong></li>
                <li>Accédez au module <strong>Ressources Humaines</strong></li>
                <li>Sélectionnez <strong>Saisie de Présence</strong> puis cliquez sur <strong>+ Nouveau</strong></li>
                <li>Renseignez la date, l'heure d'arrivée, l'heure de départ et les éventuelles remarques</li>
                <li>Cliquez sur <strong>Valider</strong></li>
            </ol>

            <div style="background-color: #fef9f0; border: 1px solid #f0d9a0; border-radius: 4px; padding: 16px 20px; margin: 0 0 24px 0;">
                <p style="margin: 0; font-size: 13px; color: #7a5c00; font-weight: 600;">Attention</p>
                <p style="margin: 6px 0 0 0; font-size: 13px; color: #7a5c00; line-height: 1.6;">
                    Le non-respect de cette échéance peut entraîner un retard dans le traitement de votre paie ainsi qu'une correction administrative de votre dossier.
                </p>
            </div>

            <p style="color: #555; font-size: 14px; line-height: 1.6; margin: 0;">
                Pour toute difficulté, veuillez contacter le département Ressources Humaines.
            </p>
        </div>

        <div style="background-color: #f5f7fa; padding: 16px 32px; border-top: 1px solid #e0e0e0;">
            <p style="margin: 0; color: #999; font-size: 12px;">Ce message est généré automatiquement par le système ERPNext — Amoaman &amp; Associés. Merci de ne pas y répondre directement.</p>
        </div>
    </div>
    """

    return subject, message


def get_relance_reminder(employee, current_day):
    emp_name = employee.get("employee_name")
    days_late = current_day - 24

    subject = f"Relance — Saisie de présence en retard de {days_late} jour(s)"

    message = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden;">

        <div style="background-color: #1a3c5e; padding: 24px 32px;">
            <p style="margin: 0; color: #ffffff; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; font-weight: 600;">Amoaman &amp; Associés — Ressources Humaines</p>
        </div>

        <div style="background-color: #c0392b; padding: 14px 32px;">
            <p style="margin: 0; color: #ffffff; font-size: 14px; font-weight: 600;">Délai dépassé — Action requise immédiatement</p>
        </div>

        <div style="padding: 32px;">
            <h2 style="margin: 0 0 8px 0; color: #1a3c5e; font-size: 20px; font-weight: 700;">Relance : saisie de présence non effectuée</h2>
            <p style="margin: 0 0 24px 0; color: #777; font-size: 13px; border-bottom: 1px solid #e0e0e0; padding-bottom: 16px;">Retard constaté : {days_late} jour(s) après l'échéance du 24 du mois</p>

            <p style="color: #333; font-size: 15px; margin: 0 0 16px 0;">Madame, Monsieur <strong>{emp_name}</strong>,</p>

            <p style="color: #333; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Malgré notre rappel précédent, votre feuille de présence du mois en cours demeure non enregistrée dans le système.
                La date limite du 24 du mois est dépassée depuis <strong style="color: #c0392b;">{days_late} jour(s)</strong>.
                Nous vous demandons de régulariser cette situation sans délai.
            </p>

            <div style="background-color: #fdf2f2; border-left: 4px solid #c0392b; padding: 16px 20px; margin: 0 0 24px 0; border-radius: 0 4px 4px 0;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #333;">
                    <tr><td style="padding: 6px 0; color: #777; width: 160px;">Statut</td><td style="padding: 6px 0; font-weight: 600; color: #c0392b;">Non saisi</td></tr>
                    <tr><td style="padding: 6px 0; color: #777;">Date limite</td><td style="padding: 6px 0; font-weight: 600;">24 du mois (dépassée)</td></tr>
                    <tr><td style="padding: 6px 0; color: #777;">Retard</td><td style="padding: 6px 0; font-weight: 600; color: #c0392b;">{days_late} jour(s)</td></tr>
                    <tr><td style="padding: 6px 0; color: #777;">Action requise</td><td style="padding: 6px 0; font-weight: 600; color: #c0392b;">Immédiate</td></tr>
                </table>
            </div>

            <p style="color: #333; font-size: 14px; font-weight: 600; margin: 0 0 10px 0;">Procédure de régularisation :</p>
            <ol style="color: #333; font-size: 14px; line-height: 1.8; margin: 0 0 24px 0; padding-left: 20px;">
                <li>Connectez-vous à <strong>ERPNext</strong></li>
                <li>Accédez au module <strong>Ressources Humaines &rsaquo; Saisie de Présence</strong></li>
                <li>Créez une nouvelle saisie et renseignez toutes les données manquantes</li>
                <li>Cliquez sur <strong>Valider</strong></li>
            </ol>

            <div style="background-color: #fef9f0; border: 1px solid #f0d9a0; border-radius: 4px; padding: 16px 20px; margin: 0 0 24px 0;">
                <p style="margin: 0; font-size: 13px; color: #7a5c00; font-weight: 600;">Conséquences potentielles</p>
                <ul style="margin: 6px 0 0 0; padding-left: 18px; font-size: 13px; color: #7a5c00; line-height: 1.8;">
                    <li>Retard ou suspension du traitement de la paie</li>
                    <li>Demande formelle du département Ressources Humaines</li>
                    <li>Note administrative versée au dossier</li>
                </ul>
            </div>

            <p style="color: #555; font-size: 14px; line-height: 1.6; margin: 0;">
                Pour toute difficulté, veuillez contacter le département Ressources Humaines dans les plus brefs délais.
            </p>
        </div>

        <div style="background-color: #f5f7fa; padding: 16px 32px; border-top: 1px solid #e0e0e0;">
            <p style="margin: 0; color: #999; font-size: 12px;">Ce message est généré automatiquement par le système ERPNext — Amoaman &amp; Associés. Merci de ne pas y répondre directement.</p>
        </div>
    </div>
    """

    return subject, message


def log_reminder_sent(employee_id, subject, email):
    try:
        doc = frappe.get_doc({
            "doctype": "Attendance Reminder Log",
            "employee": employee_id,
            "subject": subject,
            "recipient_email": email,
            "sent_date": today(),
            "status": "Sent"
        })
        doc.insert(ignore_permissions=True)
    except Exception:
        pass