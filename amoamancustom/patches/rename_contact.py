import frappe
from frappe.model.rename_doc import rename_doc

def execute():
    Contacts = frappe.get_all(
        "Contact",
        fields=["name", "full_name"],
        filters={"full_name": ["!=", ""]},
    )

    for c in Contacts:
        old = c.name
        new = (c.full_name or "").strip()

        if not new or new == old:
            continue

        # Optionnel: nettoyer quelques caractères problématiques pour un "name"
        # new = new.replace("/", "-").replace("\\", "-")

        if frappe.db.exists("Contact", new):
            # Si un Contact avec ce nom existe déjà, au choix:
            # - soit tu merges
            rename_doc("Contact", old, new, merge=True, force=True, ignore_permissions=True)
            # - soit tu skips (à la place du merge)
            # continue
        else:
            rename_doc("Contact", old, new, force=True, ignore_permissions=True)

    # Pas obligatoire en patch (Frappe gère la transaction), mais ok si tu veux:
    # frappe.db.commit()
