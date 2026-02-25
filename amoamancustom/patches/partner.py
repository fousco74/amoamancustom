import frappe

def execute():
    # On ne récupère que les champs utiles
    partners = frappe.get_all("Sales Partner", fields=["name", "partner_name"])

    for p in partners:
        if not p.partner_name:
            continue

        address_name = f"{p.partner_name}-Facturation"

        # Vérifie que l'adresse existe
        if not frappe.db.exists("Address", address_name):
            continue

        address = frappe.get_doc("Address", address_name)

        # Évite les doublons de lien
        already_linked = any(
            l.link_doctype == "Sales Partner" and l.link_name == p.name
            for l in address.links
        )
        if already_linked:
            continue

        address.append("links", {
            "link_doctype": "Sales Partner",
            "link_name": p.name,
            "link_title": p.company_name,
        })

        address.save(ignore_permissions=True)

    frappe.db.commit()
