# Copyright (c) 2026, Amoaman & Associés and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class AttendanceReminderLog(Document):
	"""Trace des rappels de saisie de présence envoyés.

	Sert de source de déduplication pour
	amoamancustom/schedulers/attendance_reminder.py. Auparavant, la
	déduplication interrogeait `tabEmail Queue` sur « n'importe quel message
	référençant cet employé », ce qui la rendait sensible à tout autre mail
	portant la même référence — les rappels d'anniversaire et de jours fériés,
	notamment, qui référencent eux aussi l'employé.
	"""

	pass
