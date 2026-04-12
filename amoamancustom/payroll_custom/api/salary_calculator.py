"""
Calculateur de Sursalaire — Calcul inverse du bulletin de salaire ERPNext.

Reproduit FIDÈLEMENT la logique de SalarySlip.calculate_net_pay() / add_structure_components()
telle qu'implémentée dans HRMS (hrms/payroll/doctype/salary_slip/salary_slip.py).

Points de conformité ERPNext :
  - whitelisted_globals  : identique à SalarySlip.__init__
  - get_data_for_eval    : contexte SSA → slip → employee → abbr_map
  - eval_condition_and_formula : condition/formule séparées, retour None si condition fausse
  - add_structure_component :
      • statistical_component : dans le contexte uniquement, hors tableau
      • depends_on_payment_days : prorata appliqué à TOUTES les composantes
        (formule ou montant fixe) via update_component_amount_based_on_payment_days
      • do_not_include_in_total : visible dans le tableau mais hors brut
  - Ordre de calcul : gains d'abord → gross_pay → retenues → net
"""

import calendar
import frappe
from frappe import _
from frappe.utils import (
    flt, cint, getdate, today as frappe_today,
    get_first_day, get_last_day, rounded,
)
from math import ceil, floor
from datetime import date


# ---------------------------------------------------------------------------
# Whitelist identique à SalarySlip.whitelisted_globals (HRMS)
# + fonctions supplémentaires couramment utilisées dans les formules
# ---------------------------------------------------------------------------
_WHITELISTED = {
    "__builtins__": {},
    # Identique à HRMS
    "int": int,
    "float": float,
    "long": int,
    "round": round,
    "rounded": rounded,
    "date": date,
    "getdate": getdate,
    "get_first_day": get_first_day,
    "get_last_day": get_last_day,
    "ceil": ceil,
    "floor": floor,
    # Fonctions mathématiques standard souvent utilisées dans les formules
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    # Utilitaires Frappe
    "flt": flt,
    "cint": cint,
}


def _safe_eval(expr: str, local_data: dict, is_condition: bool = False):
    """
    Évalue une expression comme ERPNext le fait dans eval_condition_and_formula().

    Signature identique à HRMS :
        eval(code, eval_globals, eval_locals)

    Si is_condition=True et que la variable est introuvable (NameError), retourne True :
    cela reproduit le comportement ERPNext où un champ employé est toujours défini en
    production — en simulation on inclut la composante plutôt que de l'exclure.

    Retourne None si l'expression est vide ou en cas d'erreur non-NameError.
    """
    if not expr:
        return None
    try:
        return eval(expr, dict(_WHITELISTED), dict(local_data))  # nosec
    except NameError as e:
        if is_condition:
            # Variable absente du contexte simulé : on inclut la composante (comme en prod)
            frappe.logger("salary_calculator").info(
                f"_safe_eval condition NameError (inclus) — expr={expr!r} — {e}"
            )
            return True
        frappe.logger("salary_calculator").warning(
            f"_safe_eval NameError — expr={expr!r} — {e}"
        )
        return None
    except Exception as e:
        frappe.logger("salary_calculator").warning(
            f"_safe_eval error — expr={expr!r} — {type(e).__name__}: {e}"
        )
        return None


# ---------------------------------------------------------------------------
# Détection des variables requises selon la structure
# ---------------------------------------------------------------------------

_VARIABLE_GROUPS = [
    {
        "id": "periode",
        "label": "Période de paie",
        "description": "Nécessaire pour les composantes conditionnelles (ex. gratification de décembre).",
        "triggers": ["getdate", "start_date", ".month", ".year"],
        "fields": [
            {
                "fieldname": "mois_paie",
                "label": "Mois de paie",
                "fieldtype": "Date",
                "description": "Choisir n'importe quel jour du mois cible",
            }
        ],
    },
    {
        "id": "anciennete",
        "label": "Ancienneté du salarié",
        "description": "Affecte la prime d'ancienneté et la gratification.",
        "triggers": [
            "custom_length_of_service_year",
            "custom_length_of_service_month",
            "prim_ancienn",
            "anciennete",
            "length_of_service",
        ],
        "fields": [
            {"fieldname": "anciennete_annees", "label": "Années d'ancienneté", "fieldtype": "Int", "default": 0},
            {
                "fieldname": "anciennete_mois_supp",
                "label": "Mois supplémentaires",
                "fieldtype": "Int",
                "default": 0,
                "description": "Mois au-delà des années complètes",
            },
        ],
    },
    {
        "id": "conges",
        "label": "Congés payés validés",
        "description": "Utilisé pour le calcul de l'indemnité de congés payés.",
        "triggers": ["custom_validated_paid_leave_days", "custom_left", "leave_balance", "indem_cong", "conge"],
        "fields": [
            {
                "fieldname": "conges_valides",
                "label": "Jours de congés payés validés",
                "fieldtype": "Int",
                "default": 0,
                "description": "0 si pas de congés en liquidation ce mois",
            }
        ],
    },
    {
        "id": "jours_paie",
        "label": "Jours de paie",
        "description": "Prorata si le salarié n'a pas travaillé le mois entier.",
        "triggers": ["payment_days", "depends_on_payment_days"],
        "fields": [
            {"fieldname": "payment_days", "label": "Jours de paie", "fieldtype": "Int", "default": 26},
            {"fieldname": "total_working_days", "label": "Total jours ouvrables", "fieldtype": "Int", "default": 26},
        ],
    },
    {
        "id": "avance",
        "label": "Avance sur salaire",
        "description": "Montant de l'avance sur salaire à déduire.",
        "triggers": ["__avance_detected__"],
        "fields": [
            {"fieldname": "avance_salaire", "label": "Avance sur salaire", "fieldtype": "Currency", "default": 0}
        ],
    },
    {
        "id": "transport",
        "label": "Prime de Transport",
        "description": "Montant fixe de la prime de transport (non calculé par formule dans cette structure).",
        "triggers": ["__transport_fixed__"],
        "fields": [
            {"fieldname": "prime_transport", "label": "Prime de Transport", "fieldtype": "Currency", "default": 0}
        ],
    },
]


@frappe.whitelist()
def get_required_variables(salary_structure: str) -> list:
    """
    Analyse les formules et conditions de la structure salariale puis retourne
    les groupes de variables supplémentaires nécessaires au calcul.
    """
    ss = frappe.get_doc("Salary Structure", salary_structure)
    all_rows = list(ss.earnings) + list(ss.deductions)
    all_text = " ".join(
        (d.formula or "") + " " + (d.condition or "")
        for d in all_rows
    ).lower()

    has_avance = bool(_find_avance_abbr(ss))
    has_payment_days_dep = any(
        cint(getattr(d, "depends_on_payment_days", 0))
        for d in all_rows
    )

    # Transport fixe : composante transport sans formule (montant statique dans la structure)
    transport_comp = _find_transport_comp(ss)
    has_transport_fixe = bool(
        transport_comp
        and not cint(getattr(transport_comp, "amount_based_on_formula", 0))
        and not (transport_comp.formula or "").strip()
    )

    result = []
    for group in _VARIABLE_GROUPS:
        if group["id"] == "avance":
            if has_avance:
                result.append(group)
            continue

        if group["id"] == "transport":
            if has_transport_fixe:
                grp = dict(group)
                grp["fields"] = [dict(f) for f in group["fields"]]
                grp["fields"][0]["default"] = flt(transport_comp.amount)
                grp["description"] = (
                    f"La structure définit un montant fixe de {flt(transport_comp.amount):,.0f}. "
                    "Modifiez si l'employé a un montant différent."
                )
                result.append(grp)
            continue

        if group["id"] == "jours_paie":
            if has_payment_days_dep or any(t in all_text for t in group["triggers"]):
                result.append(group)
            continue

        if any(t.lower() in all_text for t in group["triggers"]):
            result.append(group)

    return result


# ---------------------------------------------------------------------------
# API publiques
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_salary_components(salary_structure: str) -> dict:
    """Retourne earnings et deductions d'une structure salariale."""
    ss = frappe.get_doc("Salary Structure", salary_structure)

    def _row(d):
        return {
            "salary_component": d.salary_component,
            "abbr": d.abbr,
            "amount_based_on_formula": cint(d.amount_based_on_formula),
            "formula": d.formula or "",
            "amount": flt(d.amount),
            "condition": d.condition or "",
            "statistical_component": cint(getattr(d, "statistical_component", 0)),
            "variable_based_on_taxable_salary": cint(getattr(d, "variable_based_on_taxable_salary", 0)),
            "depends_on_payment_days": cint(getattr(d, "depends_on_payment_days", 0)),
            "do_not_include_in_total": cint(getattr(d, "do_not_include_in_total", 0)),
        }

    return {
        "earnings": [_row(d) for d in ss.earnings],
        "deductions": [_row(d) for d in ss.deductions],
    }


@frappe.whitelist()
def calculer_sursalaire(
    salary_structure: str,
    sursalaire_abbr: str,
    base,
    nombre_de_parts,
    net_cible,
    mois_paie=None,
    anciennete_annees=0,
    anciennete_mois_supp=0,
    conges_valides=0,
    payment_days=26,
    total_working_days=26,
    avance_salaire=0,
    prime_transport=0,
    grade=None,
    grade_cat=None,
    # Rétrocompatibilité : transport était un paramètre séparé, ignoré désormais
    transport=None,
) -> dict:
    """
    Calcule par dichotomie (binary search) la valeur du sursalaire permettant
    d'atteindre net_cible.

    La simulation reproduit EXACTEMENT la logique ERPNext/HRMS :
      1. Contexte construit comme get_data_for_eval (SSA + slip + employee + abbr_map)
      2. Gains traités en premier dans l'ordre de la structure
      3. gross_pay mis à jour avant les retenues
      4. Retenues traitées ensuite
      5. depends_on_payment_days appliqué à TOUTES les composantes (formule OU fixe)
         comme le fait update_component_amount_based_on_payment_days dans HRMS
    """
    base         = flt(base)
    parts        = flt(nombre_de_parts) or 1.0
    net_cible    = flt(net_cible)
    anc_annees   = flt(anciennete_annees)
    anc_mois     = flt(anciennete_mois_supp)
    conges       = flt(conges_valides)
    pay_days     = flt(payment_days) or 26.0
    work_days    = flt(total_working_days) or 26.0
    avance       = flt(avance_salaire)
    prime_transp = flt(prime_transport)
    grade_str    = str(grade or "")
    grade_cat_str = str(grade_cat or "")

    if net_cible <= 0:
        return {"success": False, "error": _("Le salaire net cible doit être positif.")}
    if base <= 0:
        return {"success": False, "error": _("Le salaire de base doit être positif.")}
    if parts > 20:
        return {
            "success": False,
            "error": _(
                "Le nombre de parts fiscales ({parts}) semble incorrect. "
                "Les valeurs habituelles sont 1, 1.5, 2, 2.5, 3… "
                "Vérifiez la saisie (évitez le point comme séparateur de milliers)."
            ).format(parts=parts),
        }

    # ── Dates de période ──────────────────────────────────────────
    d_ref      = getdate(mois_paie) if mois_paie else getdate(frappe_today())
    year, month = d_ref.year, d_ref.month
    start_date  = f"{year}-{month:02d}-01"
    last_day    = calendar.monthrange(year, month)[1]
    end_date    = f"{year}-{month:02d}-{last_day:02d}"

    # ── Chargement de la structure ────────────────────────────────
    ss             = frappe.get_doc("Salary Structure", salary_structure)
    transport_comp = _find_transport_comp(ss)
    transport_abbr = transport_comp.abbr if transport_comp else None
    avance_abbr    = _find_avance_abbr(ss)

    # Toutes les abréviations de composantes → 0
    # (équivalent de get_component_abbr_map dans HRMS)
    all_abbrs = {
        row[0]: 0.0
        for row in frappe.db.sql(
            "SELECT salary_component_abbr FROM `tabSalary Component`"
            " WHERE salary_component_abbr IS NOT NULL"
        )
    }

    # ============================================================
    # Simulation — reproduit fidèlement calculate_net_pay() + add_structure_components()
    # ============================================================
    def simulate(sursalaire_value: float) -> tuple:
        """
        Retourne (net, gross, total_retenues, gains, retenues).
        Suit exactement le flux ERPNext :
          1. get_data_for_eval → ctx
          2. earnings loop → gross
          3. gross_pay mis à jour dans ctx
          4. deductions loop → total_retenues
        """

        # ── Contexte initial — get_data_for_eval() ───────────────
        # ERPNext : data.update(SSA) → data.update(slip.as_dict()) → data.update(employee.as_dict())
        #           → data.update(component_abbr_map)
        # On fournit les équivalents des champs salary_slip et employee les plus utilisés.
        ctx = frappe._dict(all_abbrs)
        ctx.update({
            # ── Champs salary_slip.as_dict() ──
            "base":               base,
            "gross_pay":          0.0,
            "gross":              0.0,
            "net_pay":            0.0,
            "start_date":         start_date,
            "end_date":           end_date,
            "payment_days":       pay_days,
            "total_working_days": work_days,
            "payroll_frequency":  "Monthly",
            "salary_structure":   salary_structure,
            # ── Champs employee.as_dict() (custom fields) ──
            # Le simulateur n'a pas accès au document employee réel ;
            # on fournit les champs custom les plus utilisés dans les formules.
            "custom_salaire_de_base":              base,
            "custom_sursalaire":                   sursalaire_value,
            "custom_nbre_de_parts":                parts,
            "custom_length_of_service_year":       anc_annees,
            "custom_length_of_service_month":      anc_mois,
            "custom_validated_paid_leave_days":    conges,
            "custom_left":                         conges,
            "custom_leave_balance":                conges,
            # ── Grade / Catégorie (utilisés dans les conditions de composantes) ──
            # Exemple : condition `custom_catégorie_` sur le Salaire de Base
            # En production, employee.as_dict() fournit ces champs automatiquement.
            "custom_catégorie_":       grade_cat_str or 1,
            "custom_categorie_":       grade_cat_str or 1,
            "custom_categorie_grade":  grade_cat_str or 1,
            "custom_grade":            grade_str or 1,
            "custom_grade_categorie":  grade_cat_str or 1,
            # ── Alias courants dans les formules ITS / fiscalité ──
            "nombre_de_parts":    parts,
            "parts":              parts,
            "NP":                 parts,
            "np":                 parts,
            # ── Alias sursalaire ──
            "sursalaire":         sursalaire_value,
        })
        # Abréviation sursalaire initialisée (mise à jour en boucle)
        ctx[sursalaire_abbr] = sursalaire_value

        # ── GAINS (earnings) ─────────────────────────────────────
        # Reproduit add_structure_component() pour component_type="earnings"
        gains  = []
        gross  = 0.0

        for comp in ss.earnings:
            is_stat        = cint(getattr(comp, "statistical_component", 0))
            is_do_not_incl = cint(getattr(comp, "do_not_include_in_total", 0))
            is_formula     = cint(comp.amount_based_on_formula)
            depends_pd     = cint(getattr(comp, "depends_on_payment_days", 0))
            is_sursalaire  = comp.abbr == sursalaire_abbr
            is_transport   = bool(transport_abbr and comp.abbr == transport_abbr)

            # ── Condition ────────────────────────────────────────
            # is_condition=True : un NameError (champ employé absent du contexte simulé)
            # est traité comme True → la composante est incluse, comme en production.
            if comp.condition:
                if not _safe_eval(comp.condition, ctx, is_condition=True):
                    continue

            # ── Montant brut (avant prorata payment_days) ─────────
            if is_sursalaire:
                amount = sursalaire_value

            elif is_transport and prime_transp > 0 and not is_formula:
                # Override utilisateur pour transport à montant fixe
                amount = prime_transp

            elif is_formula and comp.formula:
                amount = flt(_safe_eval(comp.formula, ctx))

            else:
                amount = flt(comp.amount)

            # ── Prorata payment_days ──────────────────────────────
            # ERPNext (update_component_amount_based_on_payment_days) applique le prorata
            # à TOUTES les composantes non-sursalaire quand depends_on_payment_days est coché,
            # qu'elles soient basées sur formule ou montant fixe.
            if depends_pd and work_days and not is_sursalaire:
                amount = flt(amount * pay_days / work_days)

            # ── Mise à jour du contexte ───────────────────────────
            # ERPNext : "if amount: data[abbr] = amount"
            if amount or is_sursalaire:
                ctx[comp.abbr] = amount
            if is_sursalaire:
                ctx["custom_sursalaire"] = amount
                ctx["sursalaire"]        = amount

            # ── Statistical : dans ctx uniquement, hors tableau ───
            if is_stat:
                continue

            gains.append({
                "label":         comp.salary_component,
                "abbr":          comp.abbr,
                "amount":        amount,
                "is_sursalaire": is_sursalaire,
                "hors_brut":     bool(is_do_not_incl),
            })

            # do_not_include_in_total : visible mais exclu du brut
            if not is_do_not_incl:
                gross += amount

        # ── gross_pay dans le contexte avant les retenues ─────────
        # (ERPNext : set_gross_pay_and_base_gross_pay entre earnings et deductions)
        ctx["gross"]     = gross
        ctx["gross_pay"] = gross

        # ── RETENUES (deductions) ─────────────────────────────────
        # Reproduit add_structure_component() pour component_type="deductions"
        retenues       = []
        total_retenues = 0.0

        for comp in ss.deductions:
            is_var_tax     = cint(getattr(comp, "variable_based_on_taxable_salary", 0))
            is_stat        = cint(getattr(comp, "statistical_component", 0))
            is_do_not_incl = cint(getattr(comp, "do_not_include_in_total", 0))
            is_formula     = cint(comp.amount_based_on_formula)
            depends_pd     = cint(getattr(comp, "depends_on_payment_days", 0))
            is_avance_comp = bool(avance_abbr and comp.abbr == avance_abbr)

            # Composante via tranches d'impôt sans formule explicite
            # ERPNext délègue à calculate_variable_based_on_taxable_salary ;
            # non reproductible sans le payroll_period — on la passe à 0.
            if is_var_tax and not is_formula and not flt(comp.amount):
                retenues.append({
                    "label":  comp.salary_component,
                    "abbr":   comp.abbr,
                    "amount": 0.0,
                    "note":   "variable_based_on_taxable_salary sans formule — non calculé",
                })
                continue

            # ── Condition ─────────────────────────────────────────
            if comp.condition:
                if not _safe_eval(comp.condition, ctx, is_condition=True):
                    continue

            # ── Montant brut (avant prorata payment_days) ─────────
            if is_avance_comp:
                amount = avance

            elif is_formula and comp.formula:
                amount = flt(_safe_eval(comp.formula, ctx))

            else:
                amount = flt(comp.amount)

            # ── Prorata payment_days (même logique que les gains) ──
            if depends_pd and work_days:
                amount = flt(amount * pay_days / work_days)

            # ── Mise à jour du contexte ───────────────────────────
            if amount:
                ctx[comp.abbr] = amount

            # Statistical ou do_not_include : dans ctx mais hors totaux
            if is_stat or is_do_not_incl:
                continue

            total_retenues += amount
            retenues.append({
                "label":  comp.salary_component,
                "abbr":   comp.abbr,
                "amount": amount,
                "note":   None,
            })

        net = gross - total_retenues
        return net, gross, total_retenues, gains, retenues

    # ============================================================
    # Garde-fou : net(sursalaire=0) doit être < net_cible
    # ============================================================
    net_zero, brut_zero, ret_zero, gains_zero, ret_zero_d = simulate(0.0)

    if net_zero >= net_cible:
        return {
            "success": False,
            "error": _(
                "Sans sur-salaire, le salaire net est déjà de {net} "
                "(≥ net cible de {cible}). Vérifiez le salaire de base et le net cible."
            ).format(
                net=frappe.format(round(net_zero), {"fieldtype": "Currency"}),
                cible=frappe.format(round(net_cible), {"fieldtype": "Currency"}),
            ),
            "debug": {
                "net_sans_sursalaire": net_zero,
                "brut":                brut_zero,
                "total_retenues":      ret_zero,
                "detail_gains":        gains_zero,
                "detail_retenues":     ret_zero_d,
            },
        }

    # ============================================================
    # Dichotomie (binary search)
    # ============================================================
    low, high   = 0.0, net_cible * 5
    tolerance   = 1.0    # précision à 1 FCFA
    max_iter    = 80

    net_high, *_rest = simulate(high)
    guard = 0
    while net_high < net_cible and high < net_cible * 100:
        high        *= 2
        net_high, *_rest = simulate(high)
        guard       += 1
        if guard > 20:
            break

    if net_high < net_cible:
        return {
            "success": False,
            "error": _(
                "Impossible d'atteindre le salaire net cible avec cette structure salariale. "
                "Vérifiez que les formules de retenues sont bien configurées."
            ),
        }

    for _i in range(max_iter):
        mid          = (low + high) / 2.0
        net_mid, *_rest = simulate(mid)

        if abs(net_mid - net_cible) <= tolerance:
            break

        if net_mid < net_cible:
            low  = mid
        else:
            high = mid

    sursalaire_final                       = round((low + high) / 2.0)
    net_f, brut_f, ret_f, gains_f, ret_d_f = simulate(sursalaire_final)

    return {
        "success":         True,
        "sursalaire":      sursalaire_final,
        "brut":            brut_f,
        "total_retenues":  ret_f,
        "net_calcule":     net_f,
        "net_cible":       net_cible,
        "detail_gains":    gains_f,
        "detail_retenues": ret_d_f,
        "contexte": {
            "start_date":        start_date,
            "is_decembre":       month == 12,
            "anciennete_annees": anc_annees,
            "payment_days":      pay_days,
            "total_working_days": work_days,
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_transport_comp(ss):
    """Retourne la ligne de composante transport (earning) ou None."""
    for comp in ss.earnings:
        name_l = (comp.salary_component or "").lower()
        abbr_l = (comp.abbr or "").lower()
        if "transport" in name_l or abbr_l in ("pt", "tp", "tr", "trans", "prim_trans", "indem_trans"):
            return comp
    return None


def _find_transport_abbr(ss) -> str | None:
    """Rétrocompatibilité."""
    comp = _find_transport_comp(ss)
    return comp.abbr if comp else None


def _find_avance_abbr(ss) -> str | None:
    for comp in ss.deductions:
        name_l = (comp.salary_component or "").lower()
        abbr_l = (comp.abbr or "").lower()
        if "avance" in name_l or abbr_l in ("av_sal", "avsal", "av", "avance"):
            return comp.abbr
    return None
