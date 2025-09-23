import frappe
from frappe import _
from datetime import timedelta
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


def _attendance_sets(employee: str, start_date, end_date):
    """Récupère les sets de dates par statut d'Attendance pour l’intervalle."""
    base_filters = {
        "employee": employee,
        "docstatus": 1,
        "attendance_date": ("between", [start_date, end_date]),
    }

    halfs = frappe.get_all(
        "Attendance",
        filters={**base_filters, "status": "Half Day"},
        fields=["attendance_date"],
        ignore_permissions=True,
    )
    absents = frappe.get_all(
        "Attendance",
        filters={**base_filters, "status": "Absent"},
        fields=["attendance_date"],
        ignore_permissions=True,
    )
    presents = frappe.get_all(
        "Attendance",
        filters={**base_filters, "status": ["in", ["Present", "Work From Home"]]},
        fields=["attendance_date"],
        ignore_permissions=True,
    )

    full_abs = {getdate(a.attendance_date) for a in absents}
    half_abs = {getdate(a.attendance_date) for a in halfs}
    pres_set = {getdate(a.attendance_date) for a in presents}
    return full_abs, half_abs, pres_set


def build_time_log_rows(doc):
    """
    Construit la structure de données utilisée par le template Jinja.

    Retourne un dict:
      - header_dates: liste triée de toutes les dates (colonnes du tableau)
      - header_days_count: nombre de colonnes (entier)
      - rows: liste de lignes, chacune avec:
          - 'label' (projet / type d'activité)
          - 'cells' (liste alignée sur header_dates) d’objets {date, cls, val}
      - holiday_dates: set de dates fériées
    """
    rows = []
    header_dates_set = set()

    employee = getattr(doc, "employee", None)
    holiday_dates = get_holiday_dates_for_employee(employee)

    # Prépare tous les time logs valides
    prepared = []
    for tl in (getattr(doc, "time_logs", None) or []):
        if not tl.from_time or not tl.to_time:
            continue

        start = get_datetime(tl.from_time)
        end = get_datetime(tl.to_time)
        start_date = getdate(start)
        end_date = getdate(end)

        # Tous les jours inclus (lun–dim). Ajoute tes filtres si besoin.
        business_days = [d for d in daterange(start_date, end_date)]
        if not business_days:
            continue

        prepared.append((tl, start_date, end_date, business_days))
        header_dates_set.update(business_days)

    if not prepared:
        return {
            "holiday_dates": holiday_dates,
            "header_dates": [],
            "header_days_count": 0,
            "rows": [],
        }

    # Colonnes = toutes les dates triées (liste pour Jinja)
    header_dates = sorted(header_dates_set)
    header_days_count = len(header_dates)

    # Pour limiter le nombre de requêtes, récupère les présences/absences
    # sur la borne globale min/max
    global_start = min(p[1] for p in prepared)
    global_end = max(p[2] for p in prepared)
    full_abs, half_abs, pres_set = _attendance_sets(employee, global_start, global_end)
    
   
    print("full_abs :", len(full_abs))
    print("half_abs :", len(half_abs))
    print("pres_set :", len(pres_set))

    
    # Construction des lignes alignées sur header_dates
    for tl, start_date, end_date, business_days in prepared:
        in_log = set(business_days)
        cells = []
        for d in header_dates:
            # Date en dehors de la plage du time log courant
            if d not in in_log:
                cells.append({"date": d, "cls": "bg-light", "val": ""})
                continue

            # Sécurité: si un férié se glisse, on l'affiche distinctement
            if d in holiday_dates:
                cells.append({"date": d, "cls": "bg-yellow", "val": ""})
                continue

            if d in full_abs:
                cells.append({"date": d, "cls": "bg-cyan", "val": ""})
            elif d in half_abs:
                cells.append({"date": d, "cls": "bg-cyan", "val": 0.5})
            elif d in pres_set:
                cells.append({"date": d, "cls": "", "val": 1})
            else:
                cells.append({"date": d, "cls": "", "val": ""})
                        
           

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
