import frappe
from frappe import _
from frappe.utils import getdate, get_first_day, get_last_day
from frappe.utils.data import flt
import requests
from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError


# =============================================================================
# Helpers API externe (prives)
# =============================================================================

def _handle_http_error(exc: requests.HTTPError, url: str) -> None:
    """Traduit les codes HTTP d'erreur externes en frappe.throw lisible."""
    status = exc.response.status_code if exc.response is not None else 0
    try:
        body   = exc.response.json()
        detail = body.get("message") or body.get("error") or body.get("detail") or str(body)
    except Exception:
        detail = exc.response.text if exc.response is not None else str(exc)

    frappe.log_error(f"HTTP {status} - {url}\n{detail}", "External API")

    messages = {
        400: _("Requete invalide envoyee a l'API externe (400) : {0}").format(detail),
        401: _("Non authentifie - verifiez vos credentials API (401)."),
        403: _("Acces refuse par l'API externe (403)."),
        404: _("Ressource introuvable sur l'API externe (404)."),
        422: _("Donnees rejetees par l'API externe (422) : {0}").format(detail),
        429: _("Limite de requetes atteinte (429). Reessayez plus tard."),
        500: _("Erreur interne de l'API externe (500)."),
    }
    frappe.throw(messages.get(status, _("Erreur HTTP {0} : {1}").format(status, detail)))


def _build_headers(token: str = None, api_key: str = None, extra: dict = None) -> dict:
    """Construit les headers HTTP communs pour une API externe."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if api_key:
        headers["X-API-Key"] = api_key
    if extra:
        headers.update(extra)
    return headers


# =============================================================================
# Utilitaires HTTP generiques (whitelisted)
# =============================================================================

@frappe.whitelist()
def external_get(url: str, params: dict | str = None, headers: dict | str = None, timeout: int = 10) -> dict:
    """Requete GET vers une API externe. Retourne le JSON parse."""
    params  = frappe.parse_json(params)  if isinstance(params,  str) else (params  or {})
    headers = frappe.parse_json(headers) if isinstance(headers, str) else (headers or {})
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Timeout:
        frappe.log_error(f"Timeout GET {url}", "External API")
        frappe.throw(_("L'API externe n'a pas repondu dans les delais (GET {0})").format(url))
    except RequestsConnectionError:
        frappe.log_error(f"ConnectionError GET {url}", "External API")
        frappe.throw(_("Impossible de joindre l'API externe : {0}").format(url))
    except requests.HTTPError as e:
        _handle_http_error(e, url)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"external_get: {url}")
        frappe.throw(_("Erreur inattendue lors de l'appel API externe."))


@frappe.whitelist()
def external_post(url: str, payload: dict | str = None, headers: dict | str = None, timeout: int = 15) -> dict:
    """Requete POST vers une API externe."""
    payload = frappe.parse_json(payload) if isinstance(payload, str) else (payload or {})
    headers = frappe.parse_json(headers) if isinstance(headers, str) else (headers or {})
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Timeout:
        frappe.log_error(f"Timeout POST {url}", "External API")
        frappe.throw(_("Timeout lors du POST vers {0}").format(url))
    except RequestsConnectionError:
        frappe.log_error(f"ConnectionError POST {url}", "External API")
        frappe.throw(_("Impossible de joindre : {0}").format(url))
    except requests.HTTPError as e:
        _handle_http_error(e, url)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"external_post: {url}")
        frappe.throw(_("Erreur inattendue lors du POST API externe."))


@frappe.whitelist()
def external_put(url: str, payload: dict | str = None, headers: dict | str = None, timeout: int = 15) -> dict:
    """Requete PUT vers une API externe."""
    payload = frappe.parse_json(payload) if isinstance(payload, str) else (payload or {})
    headers = frappe.parse_json(headers) if isinstance(headers, str) else (headers or {})
    try:
        resp = requests.put(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Timeout:
        frappe.log_error(f"Timeout PUT {url}", "External API")
        frappe.throw(_("Timeout lors du PUT vers {0}").format(url))
    except requests.HTTPError as e:
        _handle_http_error(e, url)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"external_put: {url}")
        frappe.throw(_("Erreur inattendue lors du PUT API externe."))


@frappe.whitelist()
def external_delete(url: str, headers: dict | str = None, timeout: int = 10) -> dict:
    """Requete DELETE vers une API externe."""
    headers = frappe.parse_json(headers) if isinstance(headers, str) else (headers or {})
    try:
        resp = requests.delete(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json() if resp.content else {"status": "deleted"}
    except Timeout:
        frappe.log_error(f"Timeout DELETE {url}", "External API")
        frappe.throw(_("Timeout lors du DELETE vers {0}").format(url))
    except requests.HTTPError as e:
        _handle_http_error(e, url)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"external_delete: {url}")
        frappe.throw(_("Erreur inattendue lors du DELETE API externe."))


# =============================================================================
# LinkedIn
# =============================================================================

def _get_linkedin_settings():
    """Retourne le document LinkedIn Settings (Single)."""
    settings = frappe.get_single("LinkedIn Settings")
    if not settings.base_url:
        frappe.throw(
            _("LinkedIn Settings non configure. Renseignez la Base URL."),
            frappe.ValidationError,
        )
    return settings


@frappe.whitelist(allow_guest=True)
def get_linkedln_post(limit: int = None, org_id: str = None) -> dict:
    """
    Recupere les posts d'une organisation LinkedIn via /v2/shares.

    Les parametres par defaut sont lus depuis LinkedIn Settings.

    Structure retournee par element :
        post.text.text                                         → texte
        post.created.time                                      → timestamp ms
        post.activity                                          → "urn:li:activity:..." → URL du post
        post.content.contentEntities[0].thumbnails[0].resolvedUrl → image URL

    Appel JS :
        const r = await frappe.call({
            method: "amoamancustom.api.get_linkedln_post"
        });
        console.log(r.message.elements);
    """
    try:
        settings = _get_linkedin_settings()
        token    = settings.get_token()

        resolved_org_id = org_id or settings.org_id or "70907752"
        resolved_limit  = min(int(limit or settings.default_limit or 6), 50)

        headers = _build_headers(token=token)

        url = f"{settings.base_url}/shares"
        params = {
            "q":      "owners",
            "owners": f"urn:li:organization:{resolved_org_id}",
            "count":  resolved_limit,
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            frappe.log_error(str(e), "LinkedIn feed")
            return {"elements": []}
    except Exception as e:
        frappe.log_error(str(e), "LinkedIn feed")
        return {"elements": []}


@frappe.whitelist(allow_guest=True)
def linkedin_img_proxy(url: str):
    """Proxy une image LinkedIn CDN avec le Bearer token du serveur."""
    import re
    if not re.match(r'^https://media\.licdn\.com/', url):
        frappe.local.response.http_status_code = 403
        return
    try:
        settings = _get_linkedin_settings()
        token    = settings.get_token()
        headers  = _build_headers(token=token)
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        frappe.local.response.update({
            "type":         "binary",
            "filecontent":  resp.content,
            "content_type": resp.headers.get("Content-Type", "image/jpeg"),
            "filename":     "li.jpg",
        })
    except Exception as e:
        frappe.log_error(str(e), "LinkedIn img proxy")
        frappe.local.response.http_status_code = 502


# =============================================================================
# DocType helpers
# =============================================================================

@frappe.whitelist()
def get_leave_balance(employee, leave_type="Conges Payes"):
    balance = frappe.db.get_value(
        "Leave Ledger Entry",
        filters={
            "employee":   employee,
            "leave_type": leave_type,
            "docstatus":  1,
        },
        fieldname="SUM(leaves)"
    )
    return balance if balance else 0


@frappe.whitelist()
def get_table_detail(doctype, name):
    return frappe.get_doc(doctype, name)


def _get_salary_structure_for(employee: str, as_on) -> str | None:
    """Retourne la Salary Structure affectee a la date donnee."""
    as_on = getdate(as_on)
    rows = frappe.get_all(
        "Salary Structure Assignment",
        filters={
            "employee":  employee,
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
                        leave_type: str = "Conges payes", debug: int = 0) -> float:
    """Calcule les jours de conges payes valides et met a jour Employee.custom_validated_paid_leave_days."""
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
        WHERE employee   = %s
          AND leave_type = %s
          AND status     = 'Approved'
          AND docstatus  = 1
          AND from_date <= %s
          AND to_date   >= %s
    """, (employee, leave_type, period_end, period_start), as_dict=True)

    total_days = 0.0
    for r in rows:
        try:
            fd, td = getdate(r.get("from_date")), getdate(r.get("to_date"))
            tld = float(r.get("total_leave_days") or 0)

            overlap_start = fd if fd > period_start else period_start
            overlap_end   = td if td < period_end   else period_end
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

    try:
        frappe.db.set_value(
            "Employee",
            employee,
            "custom_validated_paid_leave_days",
            total_days,
            update_modified=False,
        )
    except Exception:
        frappe.log_error("get_paid_leave_days: employee field update failed", frappe.get_traceback())

    return total_days


@frappe.whitelist()
def recalculate_salary_slip(doc):
    """Reconstruit earnings/deductions depuis la Salary Structure."""
    slip_input   = frappe.parse_json(doc)
    salary_slip  = frappe.get_doc(slip_input)

    if salary_slip.employee and salary_slip.start_date and salary_slip.end_date:
        get_paid_leave_days(
            employee=salary_slip.employee,
            start_date=salary_slip.start_date,
            end_date=salary_slip.end_date,
        )

    try:
        frappe.clear_document_cache("Employee", salary_slip.employee)
    except Exception:
        pass

    fresh_paid_days = frappe.db.get_value(
        "Employee", salary_slip.employee, "custom_validated_paid_leave_days"
    ) or 0.0

    try:
        emp = frappe.get_doc("Employee", salary_slip.employee)
        emp.custom_validated_paid_leave_days = fresh_paid_days
        salary_slip.employee_doc = emp
    except Exception:
        pass

    if salary_slip.meta.has_field("custom_validated_paid_leave_days"):
        salary_slip.set("custom_validated_paid_leave_days", flt(fresh_paid_days))

    salary_slip.set("earnings",    [])
    salary_slip.set("deductions",  [])

    if not salary_slip.get("salary_structure"):
        struct = _get_salary_structure_for(salary_slip.employee, salary_slip.start_date)
        if struct:
            salary_slip.salary_structure = struct

    if hasattr(salary_slip, "set_salary_structure_doc"):
        salary_slip.set_salary_structure_doc()
    if hasattr(salary_slip, "pull_sal_struct"):
        salary_slip.pull_sal_struct()

    if hasattr(salary_slip, "calculate_component_amounts"):
        salary_slip.calculate_component_amounts("earnings")
        salary_slip.calculate_component_amounts("deductions")
    elif hasattr(salary_slip, "compute_component_wise_amount"):
        salary_slip.compute_component_wise_amount()
    else:
        salary_slip.gross_pay       = sum(flt(e.amount) for e in salary_slip.get("earnings"))
        salary_slip.total_deduction = sum(flt(d.amount) for d in salary_slip.get("deductions"))

    if hasattr(salary_slip, "calculate_net_pay"):
        salary_slip.calculate_net_pay()
    else:
        salary_slip.net_pay = flt(salary_slip.gross_pay) - flt(salary_slip.total_deduction)

    return {
        "earnings":   [row.as_dict() for row in salary_slip.earnings],
        "deductions": [row.as_dict() for row in salary_slip.deductions],
        "net_pay":    salary_slip.net_pay,
        "paid_days":  fresh_paid_days,
    }


@frappe.whitelist(allow_guest=True)
def create_entry(doctype, data):
    """
    Cree un document Frappe generique.
    Accepte les champs multi-selection envoyes comme liste.
    """
    data = frappe.parse_json(data)

    if not doctype or not isinstance(data, dict):
        frappe.throw(_("Parametres invalides : 'doctype' et 'data' (dict) requis."))

    meta      = frappe.get_meta(doctype)
    field_map = {f.fieldname: f for f in meta.fields}
    doc_data  = {}

    for fieldname, value in data.items():
        if fieldname not in field_map:
            continue
        if isinstance(value, list):
            doc_data[fieldname] = ", ".join(str(v) for v in value)
        else:
            doc_data[fieldname] = value

    doc = frappe.get_doc({"doctype": doctype, **doc_data})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "name":    doc.name,
        "doctype": doc.doctype,
        "message": _("{0} cree avec succes").format(doctype),
    }
