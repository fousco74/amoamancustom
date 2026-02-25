import frappe

def execute():
    opportunities = frappe.get_all(
        "Opportunity",
        fields=["name", "customer_name"]
    )

    for o in opportunities:
        if not o.customer_name:
            continue

        contacts = frappe.get_all(
            "Contact",
            fields=["name"],
            filters={"company_name": o.customer_name},
            order_by="modified desc",
            limit=1,
        )

        if not contacts:
            continue

        frappe.db.set_value(
            "Opportunity",
            o.name,
            "contact_person",
            contacts[0].name
        )


    frappe.db.commit()
