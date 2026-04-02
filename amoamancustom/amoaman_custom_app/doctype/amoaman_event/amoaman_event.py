import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe import _


class AmoamanEvent(WebsiteGenerator):
    website = frappe._dict(
        condition_field="is_published",
        page_title_field="title",
    )

    def validate(self):
        if not self.route:
            self.route = f"events/{self.name}"

    def get_context(self, context):
        context.is_closed = self.status in ("Closed", "Cancelled")
        context.can_apply = (
            self.is_published
            and self.status == "Published"
        )
        return context


def get_list_context(context):
    events = frappe.get_all(
        "Amoaman Event",
        filters={"is_published": 1},
        fields=[
            "name", "title", "route", "image",
            "start_date", "end_date", "start_time",
            "delivery_mode", "location_name", "city",
            "description", "short_summary", "status", "type",
        ],
        order_by="start_date asc",
    )
    context.events = events
    context.no_breadcrumbs = 1
    context.no_header = 1
    context.list_template = "amoamancustom/templates/generators/amoaman_event_list.html"
    return context


@frappe.whitelist()
def close_event(name):
    frappe.has_permission("Amoaman Event", "write", throw=True)
    doc = frappe.get_doc("Amoaman Event", name)
    doc.status = "Closed"
    doc.save(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist()
def open_event(name):
    frappe.has_permission("Amoaman Event", "write", throw=True)
    doc = frappe.get_doc("Amoaman Event", name)
    doc.status = "Published"
    doc.save(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def submit_event_application(event, full_name, email, phone=None,
                              company=None, job_title=None,
                              application_type=None, consent_to_contact=0):
    """Crée une Amoaman Application depuis le formulaire public."""
    # Vérifie que l’événement est ouvert
    ev = frappe.get_doc("Amoaman Event", event)
    if ev.status in ("Closed", "Cancelled"):
        frappe.throw(_("Les inscriptions à cet événement sont fermées."))
    if not ev.is_published:
        frappe.throw(_("Cet événement n’est pas disponible."))

    app = frappe.new_doc("Amoaman Application")
    app.program = event
    app.full_name = full_name
    app.email = email
    app.phone = phone
    app.company = company
    app.job_title = job_title
    app.application_type = application_type
    app.consent_to_contact = int(consent_to_contact)
    app.source = "Website"
    app.insert(ignore_permissions=True)
    frappe.db.commit()
    return app.name


