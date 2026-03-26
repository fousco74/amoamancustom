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
            should_send = check_send_conditions(emp["name"], current_day, reminder_type)
            
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
        "Employee Checkin",
        filters={
            "employee": employee_id,
            "docstatus": 1,  # Validé
            "checkin_date": ["between", [first_day, last_day]]
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


def check_send_conditions(employee_id, current_day, reminder_type):
    """
    Vérifie si on doit envoyer le rappel aujourd'hui
    Évite les doublons/surcharge
    """
    
    if reminder_type == "daily":
        # Envoyer tous les jours du 20-24
        return True
    
    elif reminder_type == "every_2_days":
        # Envoyer tous les 2 jours après le 24
        # Vérifier si un email a déjà été envoyé aujourd'hui
        
        last_email_sent = frappe.db.get_value(
            "Email Log",
            filters={
                "recipients": ["like", f"%{employee_id}%"],
                "subject": ["like", "%Rappel%Présence%"],
                "creation": [">=", today()]
            },
            fieldname="creation"
        )
        
        if last_email_sent:
            # Email déjà envoyé aujourd'hui, ne pas envoyer
            return False
        
        # Vérifier le dernier email envoyé
        last_emails = frappe.db.get_list(
            "Email Log",
            filters={
                "recipients": ["like", f"%{employee_id}%"],
                "subject": ["like", "%Rappel%Présence%"]
            },
            fields=["creation"],
            order_by="creation desc",
            limit=1
        )
        
        if last_emails:
            last_date = last_emails[0]["creation"]
            days_since = (getdate(today()) - getdate(last_date)).days
            
            # Envoyer si >= 2 jours depuis dernier email
            return days_since >= 2
        
        # Premier email = envoyer
        return True
    
    return False


def send_reminder_email(employee, reminder_type, current_day):
    """
    Envoie l'email de rappel avec le contenu approprié
    """
    
    user = frappe.get_doc("User", employee.get("user_id"))
    
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
    """
    Message urgent pour le 20-24 du mois
    """
    
    emp_name = employee.get("employee_name")
    
    subject = f"⏰ URGENT: Saisie de présence requise (Jour {current_day}/24)"
    
    days_remaining = 24 - current_day
    
    message = f"""
    <div style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; border-radius: 5px;">
        
        <h3 style="color: #d32f2f;">⏰ RAPPEL URGENT - Saisie de Présence</h3>
        
        <p style="color: #333;">Bonjour <strong>{emp_name}</strong>,</p>
        
        <p style="color: #d32f2f; font-weight: bold;">
            ⚠️ Vous avez encore <strong>{days_remaining} jour(s)</strong> pour saisir votre présence du mois !
        </p>
        
        <hr style="border: 1px solid #ddd;">
        
        <h4 style="color: #1976d2;">📋 Informations de Saisie:</h4>
        <ul style="background-color: #fff; padding: 15px; border-left: 4px solid #1976d2;">
            <li><strong>Période couverte:</strong> Tout le mois (du 1er au 30/31)</li>
            <li><strong>Délai limite:</strong> <span style="color: #d32f2f;"><strong>Le 24 du mois</strong></span></li>
            <li><strong>Statut actuel:</strong> ❌ NON SAISI</li>
            <li><strong>Date actuelle:</strong> {current_day}/24</li>
        </ul>
        
        <h4 style="color: #1976d2;">📝 Étapes à Suivre:</h4>
        <ol style="background-color: #e8f5e9; padding: 15px; border-radius: 3px;">
            <li>Connectez-vous à <strong>ERPNext</strong></li>
            <li>Allez dans le module <strong>Ressources Humaines</strong></li>
            <li>Sélectionnez <strong>"Saisie de Présence"</strong></li>
            <li>Cliquez sur <strong>"+ Nouveau"</strong></li>
            <li>Remplissez:
                <ul>
                    <li>📅 <strong>Date de l'enregistrement</strong></li>
                    <li>🕐 <strong>Heure d'arrivée</strong></li>
                    <li>🕑 <strong>Heure de départ</strong></li>
                    <li>💬 <strong>Remarques</strong> (optionnel)</li>
                </ul>
            </li>
            <li>Cliquez sur <strong style="color: #2e7d32;">"Valider"</strong></li>
        </ol>
        
        <div style="background-color: #fff3e0; border-left: 4px solid #f57c00; padding: 15px; margin: 15px 0;">
            <h4 style="color: #f57c00; margin-top: 0;">⚠️ Conséquences du Non-Respect du Délai:</h4>
            <ul>
                <li>❌ Retard de traitement de la paie</li>
                <li>❌ Problèmes de calcul des allocations</li>
                <li>❌ Nécessité d'une correction administrative</li>
                <li>❌ Possible retenue sur la paie du mois suivant</li>
            </ul>
        </div>
        
        <p style="color: #666; font-size: 12px;">
            <em>Cet email est envoyé automatiquement. Ne tardez pas !</em><br>
            <strong>Département Ressources Humaines</strong>
        </p>
    </div>
    """
    
    return subject, message


def get_relance_reminder(employee, current_day):
    """
    Message de relance après le 24 du mois
    Plus insistant car délai dépassé
    """
    
    emp_name = employee.get("employee_name")
    days_late = current_day - 24
    
    subject = f"🔴 URGENT - Saisie Présence EN RETARD (Jour {current_day} - {days_late}j après délai)"
    
    message = f"""
    <div style="font-family: Arial, sans-serif; background-color: #ffebee; padding: 20px; border-radius: 5px; border: 2px solid #d32f2f;">
        
        <h2 style="color: #d32f2f; text-align: center;">🔴 RELANCE URGENT</h2>
        
        <p style="color: #333; font-size: 16px;"><strong>Bonjour {emp_name},</strong></p>
        
        <div style="background-color: #d32f2f; color: white; padding: 15px; border-radius: 3px; margin: 15px 0;">
            <p style="margin: 0; font-weight: bold; font-size: 18px;">
                ⚠️ DÉLAI DÉPASSÉ: Vous êtes en retard de <strong>{days_late} jour(s)</strong>
            </p>
        </div>
        
        <hr style="border: 2px solid #d32f2f;">
        
        <h4 style="color: #d32f2f;">📊 État de Votre Saisie:</h4>
        <table style="width: 100%; border-collapse: collapse; background-color: white;">
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Statut</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #d32f2f;"><strong>❌ NON SAISI</strong></td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Date Limite</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">24 du mois (DÉPASSÉ)</td>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Retard Actuel</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #d32f2f;"><strong>{days_late} jour(s)</strong></td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Action Requise</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd; color: #d32f2f;"><strong>IMMÉDIATE</strong></td>
            </tr>
        </table>
        
        <h4 style="color: #d32f2f; margin-top: 20px;">🚨 Procédure d'Urgence:</h4>
        <ol style="background-color: #fff; padding: 15px; border-left: 4px solid #d32f2f;">
            <li><strong>Connectez-vous IMMÉDIATEMENT</strong> à ERPNext</li>
            <li>Allez dans <strong>Ressources Humaines → Saisie de Présence</strong></li>
            <li>Créez <strong>UNE NOUVELLE SAISIE</strong> pour le mois complet</li>
            <li>Remplissez <strong>TOUTES les données manquantes</strong></li>
            <li>Cliquez sur <strong>"Valider"</strong></li>
            <li><strong>Confirmez l'email</strong> de validation</li>
        </ol>
        
        <div style="background-color: #c62828; color: white; padding: 15px; border-radius: 3px; margin: 15px 0;">
            <h4 style="margin-top: 0;">❌ Implications du Non-Respect:</h4>
            <ul style="margin-bottom: 0;">
                <li>Suspension possible de la paie ce mois</li>
                <li>Demande formelle du département RH</li>
                <li>Note administrative au dossier</li>
                <li>Pénalités selon la politique d'entreprise</li>
            </ul>
        </div>
        
        <h4 style="color: #1976d2; margin-top: 20px;">💬 Besoin d'Aide?</h4>
        <p>Si vous rencontrez un problème:</p>
        <ul>
            <li>📧 <strong>Email RH:</strong> rh@company.com</li>
            <li>📞 <strong>Téléphone:</strong> +225 XX-XX-XX-XX</li>
            <li>🏢 <strong>Département:</strong> Ressources Humaines - Bureau 3</li>
        </ul>
        
        <p style="color: #d32f2f; font-weight: bold;">
            Merci de régulariser votre situation sans tarder!
        </p>
        
        <p style="color: #666; font-size: 11px; margin-top: 20px;">
            <em>Message automatisé envoyé le {current_day} du mois</em><br>
            <em>Cet email continue à être envoyé quotidiennement jusqu'à votre saisie</em>
        </p>
    </div>
    """
    
    return subject, message


def log_reminder_sent(employee_id, subject, email):
    """
    Enregistre l'envoi du rappel pour suivi
    """
    try:
        frappe.db.insert({
            "doctype": "Attendance Reminder Log",
            "employee": employee_id,
            "subject": subject,
            "recipient_email": email,
            "sent_date": today(),
            "status": "Sent"
        })
    except:
        # Table de log optionnelle
        pass