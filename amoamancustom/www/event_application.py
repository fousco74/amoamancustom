import frappe
from frappe import _


def get_context(context):
    event_name = frappe.form_dict.get("event")
    if not event_name:
        frappe.throw(_("Aucun événement spécifié."), frappe.DoesNotExistError)

    try:
        event = frappe.get_doc("Amoaman Event", event_name)
        print(f"\n\n\n {event}")
    except frappe.DoesNotExistError:
        frappe.throw(_("Événement introuvable."), frappe.DoesNotExistError)

    if not event.is_published:
        frappe.throw(_("Cet événement n'est pas disponible."), frappe.PermissionError)

    context.event = event
    context.is_closed = event.status in ("Closed", "Cancelled")
    context.title = _("Postuler — {0}").format(event.title)
    context.no_breadcrumbs = 1
    context.no_cache = 1
