import frappe
from frappe.model.rename_doc import rename_doc

def execute():
    customers = frappe.get_all(
        "Opportunity",
        fields=["name", "customer_name"],
        filters={"customer_name": ["!=", ""]},
    )

    for c in customers:
        old = c.name
        new = (c.customer_name or "").strip()

        if not new or new == old:
            continue

        # Optionnel: nettoyer quelques caractères problématiques pour un "name"
        # new = new.replace("/", "-").replace("\\", "-")

        if frappe.db.exists("Opportunity", new):
            # Si un Customer avec ce nom existe déjà, au choix:
            # - soit tu merges
            rename_doc("Opportunity", old, new, merge=True, force=True, ignore_permissions=True)
            # - soit tu skips (à la place du merge)
            # continue
        else:
            rename_doc("Opportunity", old, new, force=True, ignore_permissions=True)

    # Pas obligatoire en patch (Frappe gère la transaction), mais ok si tu veux:
    # frappe.db.commit()
