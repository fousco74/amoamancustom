import frappe
from frappe import _
from frappe.utils import getdate, get_first_day, get_last_day
import json
from frappe.utils.data import flt



@frappe.whitelist()
def get_table_detail(doctype, name):
    sales_order = frappe.get_doc(doctype, name)
    
    return sales_order


@frappe.whitelist()
def get_table_detail(doctype, name):
    sales_order = frappe.get_doc(doctype, name)
    return sales_order

def _get_salary_structure_for(employee: str, as_on) -> str | None:
    """Retourne la Salary Structure affectée à la date donnée (sans import erpnext.hr)."""
    as_on = getdate(as_on)
    rows = frappe.get_all(
        "Salary Structure Assignment",
        filters={
            "employee": employee,
            "from_date": ("<=", as_on),
            "docstatus": 1,
        },
        fields=["salary_structure", "from_date"],
        order_by="from_date desc",
        limit=1,
    )
    return rows[0]["salary_structure"] if rows else None


@frappe.whitelist()
def get_paid_leave_days(employee: str, start_date: str, end_date: str,
                        leave_type: str = "Congés payés", debug: int = 0) -> float:
    """Calcule les jours de congés payés validés et met à jour Employee.custom_validated_paid_leave_days."""
    if not employee or not start_date or not end_date:
        return 0.0

    try:
        sd, ed = getdate(start_date), getdate(end_date)
    except Exception:
        frappe.log_error("get_paid_leave_days: invalid dates", frappe.get_traceback())
        return 0.0

    if sd > ed:
        sd, ed = ed, sd

    period_start = get_first_day(sd)
    period_end   = get_last_day(ed)

    rows = frappe.db.sql("""
        SELECT name, from_date, to_date, total_leave_days
        FROM `tabLeave Application`
        WHERE employee = %s
          AND leave_type = %s
          AND status = 'Approved'
          AND docstatus = 1
          AND from_date <= %s
          AND to_date >= %s
    """, (employee, leave_type, period_end, period_start), as_dict=True)

    total_days = 0.0
    for r in rows:
        try:
            fd, td = getdate(r.get("from_date")), getdate(r.get("to_date"))
            tld = float(r.get("total_leave_days") or 0)

            overlap_start = fd if fd > period_start else period_start
            overlap_end   = td if td < period_end else period_end
            if overlap_end < overlap_start:
                continue

            cal_total   = (td - fd).days + 1
            cal_overlap = (overlap_end - overlap_start).days + 1
            if cal_total <= 0 or tld <= 0:
                continue

            total_days += (tld * cal_overlap / cal_total)
        except Exception:
            frappe.log_error("get_paid_leave_days: row processing error", frappe.get_traceback())

    total_days = round(total_days, 2)

    # Écrire sur Employee (même si = 0)
    try:
        frappe.db.set_value(
            "Employee",
            employee,
            "custom_validated_paid_leave_days",
            total_days,
            update_modified=False
        )
    except Exception:
        frappe.log_error("get_paid_leave_days: employee field update failed", frappe.get_traceback())

    return total_days


@frappe.whitelist()
def recalculate_salary_slip(doc):
    """Reconstruit earnings/deductions depuis la Salary Structure en utilisant la DERNIÈRE valeur Employee."""
    slip_input = frappe.parse_json(doc)
    salary_slip = frappe.get_doc(slip_input)

    # 1) Calcul & MAJ côté Employee (peut valoir 0)
    if salary_slip.employee and salary_slip.start_date and salary_slip.end_date:
        get_paid_leave_days(
            employee=salary_slip.employee,
            start_date=salary_slip.start_date,
            end_date=salary_slip.end_date,
            debug=0,
        )

    # 2) Purge cache + relire la valeur fraîche depuis Employee (zéro inclus)
    try:
        frappe.clear_document_cache("Employee", salary_slip.employee)
    except Exception:
        pass

    fresh_paid_days = frappe.db.get_value(
        "Employee", salary_slip.employee, "custom_validated_paid_leave_days"
    ) or 0.0

    # 3) Forcer employee_doc avec la valeur fraîche (si les formules lisent Employee)
    try:
        emp = frappe.get_doc("Employee", salary_slip.employee)
        emp.custom_validated_paid_leave_days = fresh_paid_days
        salary_slip.employee_doc = emp
    except Exception:
        pass

    # 4) (option recommandé) si le champ existe aussi sur le Slip, le poser tel quel (0 inclus)
    if salary_slip.meta.has_field("custom_validated_paid_leave_days"):
        salary_slip.set("custom_validated_paid_leave_days", flt(fresh_paid_days))

    # 5) Vider les lignes actuelles pour forcer la RECONSTRUCTION (rééval conditions)
    salary_slip.set("earnings", [])
    salary_slip.set("deductions", [])

    # 6) S’assurer que le Slip a une Salary Structure valable à la date du slip (sans import erpnext.hr)
    if not salary_slip.get("salary_structure"):
        struct = _get_salary_structure_for(salary_slip.employee, salary_slip.start_date)
        if struct:
            salary_slip.salary_structure = struct

    # 7) Charger le Salary Structure Doc puis repeupler depuis la structure
    if hasattr(salary_slip, "set_salary_structure_doc"):
        salary_slip.set_salary_structure_doc()
    if hasattr(salary_slip, "pull_sal_struct"):
        salary_slip.pull_sal_struct()

    # 8) Recalcul des montants puis du net (API v15)
    if hasattr(salary_slip, "calculate_component_amounts"):
        salary_slip.calculate_component_amounts("earnings")
        salary_slip.calculate_component_amounts("deductions")
    elif hasattr(salary_slip, "compute_component_wise_amount"):
        salary_slip.compute_component_wise_amount()
    else:
        salary_slip.gross_pay = sum(flt(e.amount) for e in salary_slip.get("earnings"))
        salary_slip.total_deduction = sum(flt(d.amount) for d in salary_slip.get("deductions"))

    if hasattr(salary_slip, "calculate_net_pay"):
        salary_slip.calculate_net_pay()
    else:
        salary_slip.net_pay = flt(salary_slip.gross_pay) - flt(salary_slip.total_deduction)

    return {
        "earnings": [row.as_dict() for row in salary_slip.earnings],
        "deductions": [row.as_dict() for row in salary_slip.deductions],
        "net_pay": salary_slip.net_pay,
        "paid_days": fresh_paid_days,  # valeur fraîche réellement utilisée
    }