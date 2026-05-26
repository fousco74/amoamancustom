# Copyright (c) 2026, KONE Fousseni and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DataCompliancePreAudit(Document):
    def validate(self):
        if self.email:
            self.email = self.email.strip().lower()
        if not self.submission_date:
            self.submission_date = frappe.utils.nowdate()

    def before_insert(self):
        if not self.status:
            self.status = "Nouveau"
