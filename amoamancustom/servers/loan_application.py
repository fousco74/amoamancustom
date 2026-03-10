import frappe

def set_status_from_workflow(doc, method=None):

    # Vérifier si workflow_state a réellement changé
    if not doc.has_value_changed("workflow_state"):
        return

    if doc.workflow_state == "Approuvé":
        doc.status = "Approved"

    elif doc.workflow_state == "Rejeté":
        doc.status = "Rejected"

    # Sauvegarder la modification sans déclencher récursion workflow
    doc.db_set("status", doc.status)