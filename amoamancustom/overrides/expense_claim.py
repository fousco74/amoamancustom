import frappe
from frappe.utils import flt
from frappe.query_builder.functions import Sum

from hrms.hr.doctype.expense_claim.expense_claim import ExpenseClaim


class CustomExpenseClaim(ExpenseClaim):
    """
    Override du DocType Expense Claim
    """

    def get_total_reimbursed_amount(self):
        """
        Calcule le montant total remboursé via :
        - Journal Entries
        - Payment Entries
        """

        # Si déjà marqué payé → retourne le total
        if self.is_paid:
            return flt(self.grand_total)

        # --- Journal Entries ---
        JournalEntryAccount = frappe.qb.DocType("Journal Entry Account")

        amount_via_jv = frappe.db.get_value(
            "Journal Entry Account",
            {
                "reference_name": self.name,
                "docstatus": 1,
            },
            Sum(
                JournalEntryAccount.debit_in_account_currency
                - JournalEntryAccount.credit_in_account_currency
            ),
        )

        # --- Payment Entries ---
        amount_via_payment_entry = frappe.db.get_value(
            "Payment Entry Reference",
            {
                "reference_name": self.name,
                "docstatus": 1,
            },
            "sum(allocated_amount)",
        )

        return flt(amount_via_jv) + flt(amount_via_payment_entry)