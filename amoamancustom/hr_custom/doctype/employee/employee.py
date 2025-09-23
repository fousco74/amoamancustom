import frappe
from frappe.utils import nowdate

def employment_type_changed(doc, method):
    """
    Déclencheur pour gérer automatiquement l'affectation d'une Leave Policy
    en fonction du type d'emploi (employment_type) de l'employé,
    en créant ou mettant à jour et validant la Leave Policy Assignment.
    """

    # Vérifier si le champ employment_type a changé
    if not doc.has_value_changed('employment_type'):
        return

    # Récupérer la configuration RH
    settings = frappe.get_single("RH Leave Settings")
    employment_type = doc.employment_type

    # Récupérer la Leave Policy existante pour cet employé
    leave_policy_assignment = frappe.get_all(
        "Leave Policy Assignment",
        fields=["name", "leave_policy", "docstatus"],
        filters={"employee": doc.name}
    )

    # Déterminer la Leave Policy appropriée en fonction du type d'emploi
    if employment_type in [settings.cdd_employment_type_id, settings.cdi_employment_type_id]:
        new_leave_policy_id = settings.cdi_or_cdd_leave_policy_id
    elif employment_type == settings.training_employment_type_id:
        new_leave_policy_id = settings.training_leave_policy_id
    else:
        new_leave_policy_id = None  # Aucun type reconnu

    # Si aucun type valide → désactiver ou annuler la Leave Policy existante
    if not new_leave_policy_id:
        if leave_policy_assignment:
            for lpa in leave_policy_assignment:
                # On annule proprement la politique existante
                frappe.db.set_value("Leave Policy Assignment", lpa.name, {
                    "active": 0,
                    "docstatus": 2  # 2 = annulé dans Frappe
                })
                frappe.logger().info(
                    f"Leave Policy Assignment {lpa.name} désactivée/annulée pour l'employé {doc.name}"
                )
        return

    # Trouver le leave period actuel
    current_leave_period = frappe.get_all(
        "Leave Period",
        filters={
            "from_date": ["<=", nowdate()],
            "to_date": [">=", nowdate()],
            "is_active": 1
        },
        fields=["name", "from_date", "to_date"],
        order_by="from_date desc",
        limit=1
    )

    if not current_leave_period:
        frappe.throw("Aucun Leave Period actif trouvé. Merci de créer ou activer un Leave Period.")

    leave_period_id = current_leave_period[0]["name"]
    from_date = current_leave_period[0]["from_date"]
    to_date = current_leave_period[0]["to_date"]

    # Si une Leave Policy Assignment existe → mise à jour et validation
    if leave_policy_assignment:
        for lpa in leave_policy_assignment:
            assignment_doc = frappe.get_doc("Leave Policy Assignment", lpa.name)
            assignment_doc.leave_policy = new_leave_policy_id
            assignment_doc.leave_period = leave_period_id
            assignment_doc.effective_from = from_date
            assignment_doc.effective_to = to_date
            assignment_doc.active = 1

            # Sauvegarder et valider
            assignment_doc.save(ignore_permissions=True)
            if assignment_doc.docstatus != 1:
                assignment_doc.submit()

            frappe.logger().info(
                f"Leave Policy Assignment mise à jour et validée pour {doc.name} → {new_leave_policy_id}"
            )

    else:
        # Sinon → création d'une nouvelle Leave Policy Assignment
        new_assignment = frappe.new_doc("Leave Policy Assignment")
        new_assignment.employee = doc.name
        new_assignment.employee_name = doc.employee_name
        new_assignment.assignment_based_on = "Leave Period"
        new_assignment.leave_period = leave_period_id
        new_assignment.effective_from = from_date
        new_assignment.effective_to = to_date
        new_assignment.leave_policy = new_leave_policy_id
        new_assignment.active = 1

        # Insérer puis soumettre
        new_assignment.insert(ignore_permissions=True)
        new_assignment.submit()

        frappe.logger().info(
            f"Nouvelle Leave Policy Assignment créée et validée pour {doc.name} → {new_leave_policy_id}"
        )
