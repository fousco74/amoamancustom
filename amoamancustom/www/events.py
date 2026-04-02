import frappe
from frappe import _


def get_context(context):
    context.events = frappe.get_all(
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
    context.title = _("Événements")
    context.no_breadcrumbs = 1
    context.no_cache = 1
