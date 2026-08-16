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

    La déduplication s'appuie sur `Attendance Reminder Log`, alimenté par
    log_reminder_sent. Elle interrogeait auparavant `tabEmail Queue` sur
    « n'importe quel message ayant reference_doctype='Employee' et
    reference_name=<employé> », ce qui était bien trop large : tout autre mail
    portant la même référence faisait croire au rappel qu'il avait déjà écrit.
    Les rappels d'anniversaire et de jours fériés, envoyés par
    amoamancustom/schedulers/hr_reminders.py, référencent précisément l'employé
    et auraient donc fait taire ce rappel-ci.
    """

    dernier_envoi = frappe.db.get_value(
        "Attendance Reminder Log",
        {"employee": employee_name, "status": "Sent"},
        "sent_date",
        order_by="sent_date desc",
    )

    # Jamais relancé : on envoie, quel que soit le rythme.
    if not dernier_envoi:
        return True

    jours_ecoules = (getdate(today()) - getdate(dernier_envoi)).days

    # Un seul rappel par jour, même si le job est relancé à la main.
    if jours_ecoules < 1:
        return False

    if reminder_type == "daily":
        return True

    if reminder_type == "every_2_days":
        return jours_ecoules >= 2

    return False

def send_reminder_email(employee, reminder_type, current_day):
    """
    Envoie le rappel. Le HTML vit dans
    amoamancustom/templates/emails/rappel_presence.html, qui étend le gabarit
    commun _base_mail.html : la mise en page et le lien d'instance sont donc
    partagés avec tous les autres mails de l'application.
    """

    user_id = employee.get("user_id")

    if not user_id:
        frappe.logger().warning(
            f"Employé {employee.get('name')} : aucun utilisateur rattaché, rappel non envoyé."
        )
        return

    email = frappe.db.get_value("User", user_id, "email")
    if not email:
        return

    relance = current_day > 24
    jours_restants = max(24 - current_day, 0)
    jours_retard = max(current_day - 24, 0)

    if relance:
        subject = f"Relance : saisie de présence en retard de {jours_retard} jour(s)"
    else:
        subject = f"Rappel : saisie de présence requise — échéance dans {jours_restants} jour(s)"

    message = frappe.render_template(
        "amoamancustom/templates/emails/rappel_presence.html",
        {
            "employe": employee,
            "ton": "relance" if relance else "urgent",
            "jours_restants": jours_restants,
            "jours_retard": jours_retard,
            "lien_saisie": frappe.utils.get_url_to_list("Attendance"),
        },
        is_path=True,
    )

    try:
        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=message,
            reference_doctype="Employee",
            reference_name=employee.get("name"),
        )
        log_reminder_sent(
            employee.get("name"),
            subject,
            email,
            "Relance" if relance else "Urgent",
        )
    except Exception:
        frappe.log_error(
            title=f"Rappel de présence en échec : {employee.get('name')}",
            message=frappe.get_traceback(),
        )


def log_reminder_sent(employee_id, subject, email, reminder_type):
    """Trace l'envoi dans Attendance Reminder Log.

    Ce journal est la source de déduplication de check_send_conditions : s'il
    n'est pas alimenté, les relances repartent tous les jours. L'échec n'est
    donc pas silencieux, contrairement à la version précédente qui l'avalait
    dans un `except` nu alors même que le doctype n'existait pas.
    """
    try:
        frappe.get_doc({
            "doctype": "Attendance Reminder Log",
            "employee": employee_id,
            "reminder_type": reminder_type,
            "subject": subject,
            "recipient_email": email,
            "sent_date": today(),
            "status": "Sent",
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(
            title="Journal des rappels de présence indisponible",
            message=(
                f"Employé {employee_id} : l'écriture dans Attendance Reminder Log a échoué. "
                "Sans ce journal, la déduplication des relances ne fonctionne plus.\n\n"
                + frappe.get_traceback()
            ),
        )
