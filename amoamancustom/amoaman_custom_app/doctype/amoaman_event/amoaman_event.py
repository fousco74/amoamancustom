import frappe
from frappe.website.website_generator import WebsiteGenerator
from frappe import _

class AmoamanEvent(WebsiteGenerator):
    website = frappe._dict(
        condition_field="is_published",
        page_title_field="title",
        # ⚠️ ici c’est le template DETAIL (/events/<name>)
        # laisse vide ou mets un vrai template détail:
        # template="amoamancustom/templates/generators/amoaman_event.html",
    )

    def validate(self):
        if not self.route:
            self.route = f"events/{self.name}"


def get_list_context(context):
    # plus safe que context.title = ...
    context.update({
        "list_template": "amoamancustom/templates/generators/amoaman_event_list.html",
        "filters": {"is_published": 1},
        # optionnel:
        # "order_by": "event_date asc",
    })
    return context


