import frappe
from frappe.utils import flt
from frappe.query_builder.functions import Sum

def get_total_reimbursed_amount(doc):
	if doc.is_paid:
		# No need to check for cancelled state here as it will anyways update status as cancelled
		return doc.grand_total
	else:
		JournalEntryAccount = frappe.qb.DocType("Journal Entry Account")
		amount_via_jv = frappe.db.get_value(
			"Journal Entry Account",
			{"reference_name": doc.name, "docstatus": 1},
			Sum(
				JournalEntryAccount.debit_in_account_currency - JournalEntryAccount.credit_in_account_currency
			),
		)

		amount_via_payment_entry = frappe.db.get_value(
			"Payment Entry Reference",
			{"reference_name": doc.name, "docstatus": 1},
			"sum(allocated_amount)",
		)

		return flt(amount_via_jv) + flt(amount_via_payment_entry)