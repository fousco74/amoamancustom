import frappe

def execute():
    customers = frappe.get_all(
        "Customer",
        fields=["name", "customer_name"]
    )

    for c in customers:
        if not c.customer_name:
            continue

        contacts = frappe.get_all(
            "Contact",
            fields=["name"],
            filters={"company_name": c.customer_name},
            order_by="modified desc",
            limit=1,
        )

        if not contacts:
            continue

        contact = frappe.get_doc("Contact", contacts[0].name)

        if any(
            l.link_doctype == "Customer" and l.link_name == c.name
            for l in contact.links
        ):
            continue

        contact.append("links", {
            "link_doctype": "Customer",
            "link_name": c.name,
            "link_title": c.customer_name,
        })

        contact.save(ignore_permissions=True)



    frappe.db.commit()
