import frappe
from frappe import _
import calendar
from frappe.utils import get_datetime, getdate, add_days

def get_holiday_dates_for_employee(employee: str) -> set:
    """Retourne l'ensemble des dates fériées (type date) pour l'employé."""
    if not employee:
        return set()

    emp = frappe.db.get_value(
        "Employee", employee, ["holiday_list", "company"], as_dict=True
    )

    holiday_list = None
    if emp:
        holiday_list = emp.holiday_list or frappe.db.get_value(
            "Company", emp.company, "default_holiday_list"
        )

    dates = set()
    if holiday_list:
        holidays = frappe.get_all(
            "Holiday",
            filters={"parent": holiday_list},
            fields=["holiday_date"],
            ignore_permissions=True,  # lecture simple
        )
        for h in holidays:
            dates.add(getdate(h.holiday_date))

    return dates


def daterange(d1, d2):
    """Itère jour par jour, bornes incluses (type date)."""
    cur = d1
    while cur <= d2:
        yield cur
        cur = add_days(cur, 1)


def _leave_sets(employee: str, start_date, end_date):
    """
    Récupère depuis Leave Application les dates de congé approuvés.
    Retourne (full_leave_dates, half_leave_dates) — deux sets de type date.
    """
    if not employee:
        return set(), set()

    # Congés journée entière
    full_leaves = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "docstatus": 1,
            "status": "Approved",
            "half_day": 0,
            "from_date": ("<=", end_date),
            "to_date": (">=", start_date),
        },
        fields=["from_date", "to_date"],
        ignore_permissions=True,
    )

    # Demi-journées de congé
    half_leaves = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "docstatus": 1,
            "status": "Approved",
            "half_day": 1,
            "half_day_date": ("between", [start_date, end_date]),
        },
        fields=["half_day_date"],
        ignore_permissions=True,
    )

    full_set = set()
    for leave in full_leaves:
        for d in daterange(getdate(leave.from_date), getdate(leave.to_date)):
            if start_date <= d <= end_date:
                full_set.add(d)

    half_set = {getdate(l.half_day_date) for l in half_leaves}

    return full_set, half_set


def _get_month_range(base_date):
    """Return (month_first_day, month_last_day) for the given date."""
    _, last_day = calendar.monthrange(base_date.year, base_date.month)
    month_start = base_date.replace(day=1)
    month_end = base_date.replace(day=last_day)
    return month_start, month_end


def build_time_log_rows(doc):
    """
    Construit la structure de données utilisée par le template Jinja.

    Retourne un dict:
      - header_dates: liste triée de toutes les dates (colonnes du tableau)
      - header_days_count: nombre de colonnes (entier)
      - rows: liste de lignes, chacune avec:
          - 'label' (projet / type d'activité)
          - 'cells' (liste alignée sur header_dates) d'objets {date, cls, val}
      - holiday_dates: set de dates fériées
    """
    rows = []

    employee = getattr(doc, "employee", None)
    holiday_dates = get_holiday_dates_for_employee(employee)

    base_date = getattr(doc, "start_date", None) or getattr(doc, "from_date", None) or getattr(doc, "posting_date", None)
    if base_date:
        base_date = getdate(base_date)
        month_start, month_end = _get_month_range(base_date)
    else:
        month_start = None
        month_end = None

    # Prépare tous les time logs valides
    prepared = []
    for tl in (getattr(doc, "time_logs", None) or []):
        if not tl.from_time or not tl.to_time:
            continue

        start = get_datetime(tl.from_time)
        end = get_datetime(tl.to_time)
        start_date = getdate(start)
        end_date = getdate(end)

        # Tous les jours inclus (lun–dim).
        business_days = [d for d in daterange(start_date, end_date)]
        if not business_days:
            continue

        prepared.append((tl, start_date, end_date, business_days))

    if not prepared:
        return {
            "holiday_dates": holiday_dates,
            "header_dates": [],
            "header_days_count": 0,
            "rows": [],
        }

    # Colonnes = mois complet (du 1er au dernier jour)
    if month_start is None:
        month_start = min(p[1] for p in prepared)
        month_end = max(p[2] for p in prepared)
    header_dates = list(daterange(month_start, month_end))
    header_days_count = len(header_dates)

    # Récupère les congés (Leave Application) sur le mois complet
    full_leave, half_leave = _leave_sets(employee, month_start, month_end)

    # Construction des lignes alignées sur header_dates
    for tl, start_date, end_date, business_days in prepared:
        in_log = set(business_days)
        cells = []

        for d in header_dates:

            # Jour férié → cellule vide distincte
            if d in holiday_dates:
                cells.append({"date": d, "cls": "bg-yellow", "val": ""})
                continue

            # Congé journée entière → vide
            if d in full_leave:
                cells.append({"date": d, "cls": "bg-cyan", "val": ""})
                continue

            # Demi-journée de congé → 0.5
            if d in half_leave:
                cells.append({"date": d, "cls": "bg-cyan", "val": 0.5})
                continue

            # Jour dans la plage du time log ou jour ouvré du mois → 1
            if d in in_log or (d.weekday() < 5 and month_start <= d <= month_end):
                cells.append({"date": d, "cls": "", "val": 1})
            else:
                cells.append({"date": d, "cls": "bg-light", "val": ""})

        label = (getattr(tl, "project", None) or getattr(doc, "parent_project", "") or "")
        if getattr(tl, "activity_type", None):
            label = f"{label} / {tl.activity_type}" if label else tl.activity_type

        rows.append({"label": label, "cells": cells})

    return {
        "holiday_dates": holiday_dates,
        "header_dates": header_dates,             # LISTE pour itérer
        "header_days_count": header_days_count,   # ENTIER pour range()
        "rows": rows,
    }
