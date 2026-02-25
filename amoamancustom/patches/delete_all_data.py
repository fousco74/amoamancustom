import frappe

def execute():
    doctypes = [
        "Customer",
        "Prospect",
        "Sales Partner",
        "Opportunity",
        "Supplier",
        "Address",
        "Contact",
    ]

    for doctype in doctypes:
        if frappe.db.table_exists(doctype):
            frappe.db.truncate(doctype)

    frappe.db.commit()
