import frappe
from frappe import _
from frappe.model.document import Document


class LinkedInSettings(Document):

    def validate(self):
        if self.default_limit and (int(self.default_limit) < 1 or int(self.default_limit) > 50):
            frappe.throw(_("Le nombre de posts doit être compris entre 1 et 50."))

        if self.base_url:
            self.base_url = self.base_url.rstrip("/")

    def get_token(self) -> str:
        """Retourne le token, leve une erreur explicite s'il est absent."""
        token = self.get_password("access_token")
        if not token:
            frappe.throw(
                _("Token LinkedIn manquant. Configurez-le dans LinkedIn Settings."),
                frappe.AuthenticationError,
            )
        return token
