# Copyright (c) 2026, KONE Fousseni and contributors
# Pre-audit de conformité — API publique (allow_guest)

import html as html_lib
import frappe
from frappe import _

QUESTIONS = [
    "Avez-vous une politique de confidentialité ou un document similaire ?",
    "Tenez-vous un registre des traitements de données personnelles ?",
    "Avez-vous déjà effectué des démarches auprès de l'ARTCI ?",
    "Les personnes concernées sont-elles informées de leurs droits ?",
    "Disposez-vous d'un Délégué à la Protection des Données (DPO) ?",
    "Vos équipes ont-elles été formées sur les obligations liées à la protection des données ?",
    "Vos contrats contiennent-ils des clauses relatives à la confidentialité et à la protection des données ?",
    "Effectuez-vous des transferts de données à l'étranger ?",
    "Avez-vous une procédure en cas de violation ou fuite de données ?",
    "Avez-vous mis en place des mesures techniques de sécurité (chiffrement, pare-feu, accès restreint, etc.) ?",
    "Avez-vous identifié toutes les données personnelles que vous collectez (site web, formulaire, RH, etc.) ?",
    "Avez-vous déjà reçu une plainte ou une demande d'accès aux données d'un client ou employé ?",
    "Disposez-vous de mentions d'information conformes sur vos formulaires papier ou en ligne ?",
    "Avez-vous un mécanisme permettant aux personnes d'exercer leurs droits (accès, rectification, opposition) ?",
    "Vos données sont-elles conservées pour une durée définie et justifiable ?",
]

_VALID_RESPONSES = {"Oui", "Non", "NSP"}


def _sanitize(value, max_len=500):
    """Strip, escape and truncate a string value."""
    return html_lib.escape(str(value or "").strip())[:max_len]


@frappe.whitelist(allow_guest=True)
def get_questions():
    """Returns the ordered list of pre-audit questions."""
    return [{"number": i + 1, "text": q} for i, q in enumerate(QUESTIONS)]


@frappe.whitelist(allow_guest=True)
def submit_pre_audit(data):
    """
    Creates a Data Compliance Pre Audit record from public form submission.
    CSRF protection is handled by Frappe (X-Frappe-CSRF-Token header).
    """
    data = frappe.parse_json(data) if isinstance(data, str) else data

    if not isinstance(data, dict):
        frappe.throw(_("Format de données invalide."))

    # ── Champs requis ──────────────────────────────────────────────────
    required_fields = {
        "company_name": _("Nom de l'entreprise"),
        "contact_person": _("Nom du contact"),
        "email": _("Email"),
    }
    for field, label in required_fields.items():
        if not str(data.get(field, "")).strip():
            frappe.throw(_("Le champ '{0}' est obligatoire.").format(label))

    # ── Validation email basique ───────────────────────────────────────
    email = str(data.get("email", "")).strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        frappe.throw(_("Adresse email invalide."))

    # ── Réponses ──────────────────────────────────────────────────────
    answers_raw = data.get("answers", [])
    if not isinstance(answers_raw, list) or len(answers_raw) < 1:
        frappe.throw(_("Aucune réponse fournie au questionnaire."))

    answer_rows = []
    seen_nums = set()

    for ans in answers_raw:
        if not isinstance(ans, dict):
            continue
        try:
            q_num = int(ans.get("question_number", 0))
        except (ValueError, TypeError):
            continue

        if q_num < 1 or q_num > len(QUESTIONS):
            continue
        if q_num in seen_nums:
            continue
        seen_nums.add(q_num)

        resp = str(ans.get("response", "NSP")).strip()
        if resp not in _VALID_RESPONSES:
            resp = "NSP"

        answer_rows.append({
            "doctype": "Data Compliance Answer",
            "question_number": q_num,
            "question": QUESTIONS[q_num - 1],
            "response": resp,
            "client_comment": _sanitize(ans.get("comment", ""), max_len=1000),
        })

    # Trier par numéro de question
    answer_rows.sort(key=lambda r: r["question_number"])

    # ── Création du document ───────────────────────────────────────────
    doc = frappe.get_doc({
        "doctype": "Data Compliance Pre Audit",
        "company_name":   _sanitize(data.get("company_name"), 200),
        "contact_person": _sanitize(data.get("contact_person"), 200),
        "role":           _sanitize(data.get("role"), 200),
        "email":          email,
        "phone":          _sanitize(data.get("phone"), 50),
        "sector":         _sanitize(data.get("sector"), 200),
        "company_size":   _sanitize(data.get("company_size"), 100),
        "submission_date": frappe.utils.nowdate(),
        "status": "Nouveau",
        "answers": answer_rows,
    })

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "success": True,
        "name": doc.name,
        "message": _("Votre pré-audit a été soumis avec succès."),
    }


@frappe.whitelist(allow_guest=True)
def save_draft(data):
    """
    Sauvegarde un brouillon côté serveur (cache Redis 24h).
    La sauvegarde principale reste côté client via localStorage.
    """
    data = frappe.parse_json(data) if isinstance(data, str) else data
    if not isinstance(data, dict):
        return {"success": False, "message": "Invalid data"}

    import hashlib, time
    sid = frappe.session.get("sid") or str(time.time())
    cache_key = "pre_audit_draft:{}".format(hashlib.md5(sid.encode()).hexdigest())
    frappe.cache().set_value(cache_key, data, expires_in_sec=86400)

    return {"success": True}
