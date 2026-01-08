import frappe
from frappe.website.website_generator import WebsiteGenerator

class AmoamanEvent(WebsiteGenerator):
    # Important si ton champ de publication n'est pas "published"
    website = frappe._dict(
        condition_field="is_published",   # ton checkbox
        page_title_field="title",   # ou le champ titre que tu utilises
    )

    def validate(self):
        # Générer la route côté serveur (stable, pas de boucle)
        if not self.route:
            self.route = f"events/{self.name}"
