import frappe
from frappe import _
from frappe.utils import get_link_to_form


def after_insert(doc, method):
    """Send email notification to all project users after project creation."""
    if not doc.users:
        return

    label = f"{doc.project_name} ({doc.name})"
    url = get_link_to_form(doc.doctype, doc.name, label)

    subject = _("New Project: {0}").format(doc.project_name)
    message = "<p>{}</p><p>{}</p>".format(
        _("A new project {0} has been created.").format(url),
        _("You have been assigned as a resource on this project."),
    )

    recipients = [user.user for user in doc.users if user.user]

    if recipients:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            reference_doctype=doc.doctype,
            reference_name=doc.name,
        )
