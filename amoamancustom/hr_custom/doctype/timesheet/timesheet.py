import frappe
from frappe import _
from datetime import timedelta
from frappe.utils import get_datetime, getdate, flt

def calculate_work_days(doc, method=None):
    # 1) Holiday List (sans permissions strictes)
    holiday_list = None
    if getattr(doc, "employee", None):
        emp = frappe.db.get_value(
            "Employee",
            doc.employee,
            ["holiday_list", "company"],
            as_dict=True
        )
        if emp:
            holiday_list = emp.holiday_list or frappe.db.get_value(
                "Company", emp.company, "default_holiday_list"
            )

    # 2) Dates fériées
    holiday_dates = set()
    if holiday_list:
        for h in frappe.get_all(
            "Holiday",
            filters={"parent": holiday_list},
            fields=["holiday_date"],
            ignore_permissions=True
        ):
            holiday_dates.add(getdate(h.holiday_date))
    print("holiday_dates :", holiday_dates)

    def daterange(d1, d2):
        cur = d1
        while cur <= d2:
            yield cur
            cur += timedelta(days=1)

    def get_absence_dates(employee, start_date, end_date):
        full_abs, half_abs = set(), set()

        # Half Day
        halfs = frappe.get_all(
            "Attendance",
            filters={
                "employee": employee,
                "docstatus": 1,
                "status": "Half Day",
                "attendance_date": ("between", [start_date, end_date]),
            },
            fields=["attendance_date"],
            ignore_permissions=True
        )

        # Absent (pleine journée)
        absents = frappe.get_all(
            "Attendance",
            filters={
                "employee": employee,
                "docstatus": 1,
                "status": "Absent",
                "attendance_date": ("between", [start_date, end_date]),
            },
            fields=["attendance_date"],
            ignore_permissions=True
        )

        for a in absents:
            full_abs.add(getdate(a.attendance_date))
        for a in halfs:
            half_abs.add(getdate(a.attendance_date))

        return full_abs, half_abs

    total_days = 0.0
    last_days = 0.0  # pour debug éventuel (dernière ligne traitée)

    for tl in getattr(doc, "time_logs", []):
        if not tl.from_time or not tl.to_time:
            continue

        # Parser
        start = get_datetime(tl.from_time) if isinstance(tl.from_time, str) else tl.from_time
        end   = get_datetime(tl.to_time)   if isinstance(tl.to_time, str)   else tl.to_time

        start_date = getdate(start)
        end_date   = getdate(end)

        # 3) Jours ouvrés (lun–ven, hors fériés) ✅ (on exclut les week-ends)
        business_days = [d for d in daterange(start_date, end_date)
                         if d.weekday() < 5 and d not in holiday_dates]
        print("Jours ouvrés (lun–ven, hors fériés) :", len(business_days))

        # 4) Absences
        full_abs, half_abs = set(), set()
        if getattr(doc, "employee", None):
            full_abs, half_abs = get_absence_dates(doc.employee, start_date, end_date)
            print("total full_abs :", len(full_abs))
            print("total half_abs :", len(half_abs) / 2)

        # 5) Jours nets
        days = len(business_days) - (len(full_abs) + len(half_abs) / 2)
        if days < 0:
            days = 0.0

        # Stocke des JOURS dans un champ custom de la ligne
        tl.days = days
        last_days = days
        total_days += days

    # 6) Totaux (parent)
    doc.total_days = total_days  # champ custom en entête si tu l’as créé
    print("TOTAL DAYS (doc):", total_days)

    return {"days": last_days, "total_days": total_days}


@frappe.whitelist()
def recalc_timesheet_row(timesheet, row_name: str):
    """Accepte soit un dict, soit un JSON string pour `timesheet`."""
    try:
        # 1) Normaliser `timesheet` en dict
        if isinstance(timesheet, str):
            timesheet = frappe.parse_json(timesheet)
        if not isinstance(timesheet, dict):
            frappe.throw(_("Paramètre 'timesheet' invalide (dict attendu)."))

        # 2) Doctypes attendus
        timesheet.setdefault("doctype", "Timesheet")
        if "time_logs" in timesheet and isinstance(timesheet["time_logs"], (list, tuple)):
            for i, tl in enumerate(timesheet["time_logs"]):
                if isinstance(tl, str):
                    tl = frappe.parse_json(tl)
                if isinstance(tl, dict):
                    tl.setdefault("doctype", "Timesheet Detail")
                    timesheet["time_logs"][i] = tl

        # 3) Construire le doc et calculer
        doc = frappe.get_doc(timesheet)
        print("recalc_timesheet_row -> row_name:", row_name)
        _ = calculate_work_days(doc)  # met à jour tl.days + doc.total_days

        # 4) Ligne ciblée + totaux
        row = next((tl for tl in doc.time_logs if tl.name == row_name), None)
        if not row:
            frappe.throw(_("Ligne introuvable après recalcul."))

        row_days = flt(getattr(row, "days", 0))
        total_days = flt(getattr(doc, "total_days", 0))

        print("days (row):", row_days)
        print("total_days (doc):", total_days)

        return {
            "days": row_days,        # jours pour la ligne
            "total_days": total_days # total sur le Timesheet
        }
    except Exception:
        frappe.log_error(frappe.get_traceback(), "recalc_timesheet_row failed")
        raise
