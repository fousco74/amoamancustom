# about.py
import frappe

def get_context(context):

    context.partners = frappe.get_all("Partner", fields="*", ignore_permissions=True)
    context.academy_events = frappe.get_all(
        "Amoaman Event",
        filters={"is_published": 1},
        fields=["name", "title", "route", "image"],
        order_by="start_date desc",
        limit_page_length=6,
        ignore_permissions=True,
    )
    return context