import frappe


def execute():
    # Vérifier si le workspace existe déjà
    if not frappe.db.exists("Workspace", "Welcome Workspace"):
        ws = frappe.get_doc({
            "doctype": "Workspace",
            "name": "Welcome Workspace",
            "title": "Welcome Workspace",
            "module": "Core",
            "public": 1,
            "sequence_id": 22,  # adapte si besoin
            "icon": "image-view",
            # Ajoute d'autres champs selon ce que tu veux afficher
        })
        ws.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.msgprint("Workspace 'Welcome Workspace' créé avec succès.")
    else:
        frappe.msgprint("Workspace 'Welcome Workspace' existe déjà.")