import frappe

def execute():
    """
    Patch pour réinitialiser le champ employment_type
    de tous les employés dans le système.
    """
    # Mise à jour directe en base pour plus de performance
    frappe.db.sql("""
        UPDATE `tabEmployee`
        SET employment_type = ''
        WHERE employment_type IS NOT NULL
    """)

    # Commit pour valider la transaction
    frappe.db.commit()

    # Log de confirmation
    frappe.logger().info("Tous les types d'emploi ont été réinitialisés avec succès.")
