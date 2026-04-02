import frappe
from frappe import _
from frappe.utils import getdate

_HOLIDAY_LIST = "Liste des jours fériés"


def _is_non_working_day(attendance_date) -> bool:
    """Retourne True si la date est dans la Holiday List (samedi, dimanche, férié)."""
    return bool(
        frappe.db.exists(
            "Holiday",
            {"parent": _HOLIDAY_LIST, "holiday_date": getdate(attendance_date)},
        )
    )


def validate(doc, method):
    """
    Empêche l'enregistrement d'une présence un jour non ouvré.

    - En création manuelle (UI) : l'utilisateur voit un message d'erreur clair.
    - En création bulk (background job) : l'exception est catchée par HRMS
      dans process_bulk_attendance_in_batches → la date est silencieusement
      ignorée et le job continue.
    """
    if _is_non_working_day(doc.attendance_date):
        frappe.throw(
            _("Le {0} est un jour non ouvré (week-end ou jour férié) : présence non enregistrée.").format(
                getdate(doc.attendance_date).strftime("%d/%m/%Y")
            )
        )
