import frappe

def execute():
    reports = frappe.get_all("Report", fields=["name"])

    for report in reports:

        exists = frappe.db.exists(
            "Has Role",
            {
                "parent": report["name"],
                "parenttype": "Report",
                "role": "Directeur Général"
            }
        )

        if not exists:
            row = frappe.get_doc({
                "doctype": "Has Role",
                "parent": report["name"],
                "parenttype": "Report",
                "parentfield": "roles",
                "role": "Directeur Général"
            })

            row.db_insert()

    frappe.db.commit()