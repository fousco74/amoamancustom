import frappe
from frappe.model.rename_doc import rename_doc

def execute():
    suppliers = frappe.get_all(
        "Supplier",
        fields=["name", "supplier_name"],
        filters={"supplier_name": ["!=", ""]},
    )

    for s in suppliers:
        old = s.name
        new = (s.supplier_name or "").strip()

        if not new or new == old:
            continue

        # Optionnel: nettoyer quelques caractères problématiques pour un "name"
        # new = new.replace("/", "-").replace("\\", "-")

        if frappe.db.exists("Supplier", new):
            # Si un supplier avec ce nom existe déjà, au choix:
            # - soit tu merges
            rename_doc("Supplier", old, new, merge=True, force=True, ignore_permissions=True)
            # - soit tu skips (à la place du merge)
            # continue
        else:
            rename_doc("Supplier", old, new, force=True, ignore_permissions=True)

    # Pas obligatoire en patch (Frappe gère la transaction), mais ok si tu veux:
    # frappe.db.commit()
