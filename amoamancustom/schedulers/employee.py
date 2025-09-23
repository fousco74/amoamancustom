import frappe
from dateutil.relativedelta import relativedelta
from frappe.utils import getdate, today

def set_seniority():
    """Met à jour la durée de service (ancienneté) des employés"""

    # Récupération de tous les employés nécessaires
    employees = frappe.get_all(
        "Employee",
        fields=[
            "name",
            "date_of_joining",
            "status",
            "relieving_date",
            "custom_length_of_service",
            "custom_length_of_service_year",
            "custom_length_of_service_month",
            "custom_has_seniority_bonus"
        ]
    )

    for emp in employees:
        # Vérification de la date d'embauche
        if not emp.date_of_joining:
            continue

        d1 = getdate(emp.date_of_joining)
        d2 = getdate(today()) if emp.status == "Active" else getdate(emp.relieving_date) if emp.relieving_date else None

        if not d2 or d2 < d1:
            continue  # évite les incohérences

        # Calcul de la différence
        diff = relativedelta(d2, d1)

        # Construction du texte d'ancienneté
        parts = []
        if diff.years:
            parts.append(f"{diff.years} an{'s' if diff.years > 1 else ''}")
        if diff.months:
            parts.append(f"{diff.months} mois")
        if diff.days:
            parts.append(f"{diff.days} jour{'s' if diff.days > 1 else ''}")

        seniority_text = ", ".join(parts) if parts else "0 jour"

        # Détermination du droit à la prime d'ancienneté
        has_bonus = diff.years >= 2

        # Mise à jour directe dans la base pour plus d'efficacité
        frappe.db.set_value(
            "Employee",
            emp.name,
            {
                "custom_length_of_service": seniority_text,
                "custom_length_of_service_year": diff.years,
                "custom_length_of_service_month": diff.months,
                "custom_has_seniority_bonus": has_bonus
            },
            update_modified=False
        )

    # Commit final pour toutes les mises à jour
    frappe.db.commit()
    frappe.logger().info("Ancienneté des employés mise à jour avec succès.")
