import frappe

def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    if "System Manager" in frappe.get_roles(user):
        return ""

    return f"""
        (
            `tabProject`.`owner` = {frappe.db.escape(user)}
            OR EXISTS (
                SELECT 1
                FROM `tabProject User` pu
                WHERE pu.parent = `tabProject`.name
                AND pu.user = {frappe.db.escape(user)}
            )
        )
    """