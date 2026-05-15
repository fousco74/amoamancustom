import frappe

def execute():
    reports = frappe.get_all("Report", fields=["name"])

    for report in reports:
        doc = frappe.get_doc("Report", report["name"])

        existing_roles = [r.role for r in doc.roles]

        if "Directeur Général" not in existing_roles:
            doc.append("roles", {
                "role": "Directeur Général"
            })

            doc.save(ignore_permissions=True)

    frappe.db.commit()