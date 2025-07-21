# Copyright (c) 2025, KONE Fousseni and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TrainingAttestation(Document):
    
	def get_page_info(self):
		return {
			"title": self.name or "Training Attestation",
			"route": f"/training-attestation/{self.name}",
			"published": True
		}
