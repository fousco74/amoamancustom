# apps/amoamancustom/amoamancustom/recette/donnees.py
"""
Jeu de données de recette : crée, sans envoyer de mail, un document « témoin »
par notification (native ou custom) afin de pouvoir déclencher et vérifier chaque
mail en local (Mailpit), puis tout annuler proprement.

    bench --site <site> execute amoamancustom.recette.donnees.generer
    bench --site <site> execute amoamancustom.recette.donnees.restaurer

`generer()` mute les mails (`frappe.flags.mute_emails`) pendant la création : on ne
veut pas que l'insertion déclenche déjà les notifications ; c'est le rôle de
`declencher.py`. Le journal des documents créés est écrit dans
`…/private/backups/journal_recette.json` pour être relu par `declencher.py` et
servir de référentiel (quel document déclenche quel mail).

`restaurer()` supprime ces documents de test et remet les dates anniversaire /
ancienneté modifiées pour les rappels RH. Le retour à l'état d'origine reste
garanti par le backup `--with-files` pris avant la phase 2.
"""

import json
from datetime import date, datetime

import frappe
from frappe.utils import add_days, add_months, today, getdate

COMPAGNIE = frappe.db.get_default("company") or "AMOAMAN & ASSOCIES"
DEVISES = frappe.db.get_default("currency") or "XOF"

EMPLOYE_PRINCIPAL = "A7"          # Ahou Solange KOUAKOU
EMAIL_PRINCIPAL = "skouakou@amoaman.com"
EMPLOYE_ANCIENNETE = "A21"        # Amey ANOMA
EMAIL_ANCIENNETE = "eanoma@amoaman.com"

LEAVE_TYPE = "Congés Maternités"
SALARY_COMP = "Arrear"
ITEM = "Formation-2026-00001"
PROGRAMME_WEBINAIRE = "AM-EVENT-2026-00003"

FICHIER_JOURNAL = "private/backups/journal_recette.json"

JOURNAL = []
MUTATIONS = []   # [(doctype, name, champ, valeur_d_origine)]


def _note(notification, doctype, nom, destinataire, evenement, champ=None, valeur=None):
    JOURNAL.append({
        "notification": notification,
        "doctype": doctype,
        "document": nom,
        "destinataire_attendu": destinataire,
        "evenement": evenement,
        "champ_declencheur": champ,
        "valeur_declencheur": valeur,
    })


def _json_default(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    return str(o)


def _ecrire_journal():
    chemin = frappe.get_site_path(FICHIER_JOURNAL)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"journal": JOURNAL, "mutations": MUTATIONS}, f, ensure_ascii=False, indent=2, default=_json_default)
    return chemin


def generer():
    """Crée tous les documents témoins et retourne le journal (sans envoyer de mail)."""
    JOURNAL.clear()
    MUTATIONS.clear()
    # `mute_emails` seul ne suffit pas : frappe.sendmail met quand même en file,
    # seul l'envoi est mué. C'est `run_notifications` qui saute réellement la
    # notification (et donc la mise en file) quand `in_import` ET `mute_emails`
    # sont posés ensemble (voir frappe/model/document.py). On pose les deux pour
    # ne RIEN mettre en file pendant la création — c'est le rôle de declencher.py.
    frappe.flags.mute_emails = True
    frappe.flags.in_import = True
    try:
        _entretien_depart()
        _formation()
        _avis_formation()
        _prime_fidelisation()
        _demande_materiel()
        _exercice_fiscal()
        _contrat()
        _conge()
        _ticket_hd()
        _contact()
        _candidat()
        _webinaire()
        _mutations_anniversaires()
    finally:
        frappe.flags.mute_emails = False
        frappe.flags.in_import = False

    frappe.db.commit()
    chemin = _ecrire_journal()

    print(f"=== {len(JOURNAL)} documents de recette créés ===")
    for e in JOURNAL:
        print(f"  • {e['notification']:<40} {e['doctype']} {e['document']}")
    print(f"Journal écrit : {chemin}")
    return JOURNAL


# --- Création des documents -------------------------------------------------

def _muter(doctype, nom, champ, valeur):
    """Modifie un champ en base (enregistré pour restauration, y compris vers NULL)."""
    origine = frappe.db.get_value(doctype, nom, champ)
    frappe.db.set_value(doctype, nom, champ, valeur)
    MUTATIONS.append([doctype, nom, champ, origine])  # origine peut être None


def _entretien_depart():
    nom = frappe.db.exists("Exit Interview", {"employee": EMPLOYE_PRINCIPAL, "date": add_days(today(), 1)})
    if nom:
        _note("Entretien de départ programmé", "Exit Interview", nom, EMAIL_PRINCIPAL, "Days Before")
        return
    # La validation HRMS exige une date de sortie sur l'employé. On la pose loin
    # dans le futur pour ne pas entrer en conflit avec les autres dates de paie.
    _muter("Employee", EMPLOYE_PRINCIPAL, "relieving_date", add_months(today(), 6))
    d = frappe.get_doc({
        "doctype": "Exit Interview",
        "employee": EMPLOYE_PRINCIPAL,
        "company": COMPAGNIE,
        "status": "Scheduled",
        "date": add_days(today(), 1),
        "email": EMAIL_PRINCIPAL,
    }).insert(ignore_permissions=True)
    _note("Entretien de départ programmé", "Exit Interview", d.name, EMAIL_PRINCIPAL, "Days Before")


def _formation():
    d = frappe.get_doc({
        "doctype": "Training Event",
        "event_name": "Formation recette notification",
        "event_status": "Scheduled",
        "type": "Workshop",
        "location": "Abidjan",
        "start_time": "2026-09-08 09:00:00",
        "end_time": "2026-09-08 17:00:00",
        "introduction": "Formation de recette (déclenchement de mail).",
        # `employee_emails` est recalculé par HRMS à partir de la table enfant
        # `employees` (set_employee_emails) : on renseigne donc l'employé.
        "employees": [{"employee": EMPLOYE_PRINCIPAL}],
    }).insert(ignore_permissions=True)
    d.submit()
    _note("Formation programmée", "Training Event", d.name, EMAIL_PRINCIPAL, "Submit")


def _avis_formation():
    ev = frappe.db.get_value("Training Event", {"event_name": "Formation recette notification"}, "name")
    d = frappe.get_doc({
        "doctype": "Training Result",
        "training_event": ev,
        # idem : `employee_emails` est dérivé de la table enfant `employees`.
        "employees": [{"employee": EMPLOYE_PRINCIPAL}],
    }).insert(ignore_permissions=True)
    _note("Partagez votre avis sur la formation", "Training Result", d.name, EMAIL_PRINCIPAL, "Submit")


def _prime_fidelisation():
    d = frappe.get_doc({
        "doctype": "Retention Bonus",
        "employee": EMPLOYE_PRINCIPAL,
        "company": COMPAGNIE,
        "salary_component": SALARY_COMP,
        "bonus_amount": 100000,
        "bonus_payment_date": add_days(today(), 14),
        "currency": DEVISES,
    }).insert(ignore_permissions=True)
    d.submit()
    _note("Prime de fidélisation à venir", "Retention Bonus", d.name, "Rôle HR Manager", "Days Before")


def _demande_materiel():
    d = frappe.get_doc({
        "doctype": "Material Request",
        "naming_series": "MAT-MR-.YYYY.-",
        "material_request_type": "Purchase",
        "company": COMPAGNIE,
        "transaction_date": today(),
        "items": [{
            "item_code": ITEM,
            "qty": 1,
            "schedule_date": today(),
        }],
    }).insert(ignore_permissions=True)
    _note("Demande de matériel reçue", "Material Request", d.name, "Rôle Stock Manager", "Value Change", "status", "Received")


def _exercice_fiscal():
    nom = frappe.db.exists("Fiscal Year", "2027")
    if not nom:
        d = frappe.get_doc({
            "doctype": "Fiscal Year",
            "year": "2027",
            "year_start_date": "2027-01-01",
            "year_end_date": "2027-12-31",
            "auto_created": 1,
        }).insert(ignore_permissions=True)
        nom = d.name
    _note("Nouvel exercice fiscal", "Fiscal Year", nom, "Rôles Accounts Manager + User", "New")


def _contrat():
    nom = frappe.db.exists("Contract", {"party_name": EMPLOYE_PRINCIPAL, "party_type": "Employee"})
    if not nom:
        d = frappe.get_doc({
            "doctype": "Contract",
            "party_type": "Employee",
            "party_name": EMPLOYE_PRINCIPAL,
            "contract_terms": "Contrat de recette (déclenchement de mail).",
            "start_date": add_days(today(), -365),
            "end_date": add_days(today(), 5),
            # `is_signed` sinon `update_contract_status` force status="Unsigned"
            # et la condition « doc.status == 'Active' » de la notification échoue.
            "is_signed": 1,
        }).insert(ignore_permissions=True)
        nom = d.name
    _note("Contrat proche expiration", "Contract", nom, "Rôle HR Manager + owner", "Days Before")


def _conge():
    d = frappe.get_doc({
        "doctype": "Leave Application",
        "naming_series": "HR-LAP-.YYYY.-",
        "employee": EMPLOYE_PRINCIPAL,
        "leave_type": LEAVE_TYPE,
        "company": COMPAGNIE,
        "from_date": add_days(today(), 3),
        "to_date": add_days(today(), 5),
        "posting_date": today(),
        "status": "Open",
    }).insert(ignore_permissions=True)
    # Un seul document sert aux 3 notifications « congés » (workflow_state).
    # Les valeurs doivent correspondre AUX ÉTATS FRANÇAIS du workflow (les filtres
    # des notifications comparent doc.workflow_state à « En attente DG/RH/Approuvé »).
    _note("Demande de congés - en attente DG MAIL", "Leave Application", d.name, "Rôle Directeur Général", "Value Change", "workflow_state", "En attente DG")
    _note("Demande de congés - en attente RH MAIL", "Leave Application", d.name, "Rôles HR Manager + DG", "Value Change", "workflow_state", "En attente RH")
    _note("Validation Demande de congés", "Leave Application", d.name, "Rôle HR Manager", "Value Change", "workflow_state", "Approuvé")


def _ticket_hd():
    d = frappe.get_doc({
        "doctype": "HD Ticket",
        "subject": "Ticket de recette notification",
    }).insert(ignore_permissions=True)
    _note("New HD ticket", "HD Ticket", d.name, "Rôles Helpdesk Contact + Agent", "New")


def _contact():
    d = frappe.get_doc({
        "doctype": "Contact Us",
        "first_name": "Test Recette",
        "last_name": "Notification",
        "email": "contact-recette@amoaman.test",
        "message": "Message de recette (déclenchement de mail).",
    }).insert(ignore_permissions=True)
    _note("Contact Notification", "Contact Us", d.name, "Rôle HR Manager", "Save")


def _candidat():
    d = frappe.get_doc({
        "doctype": "Job Applicant",
        "applicant_name": "Candidat Recette Notification",
        "email_id": "candidat-recette@amoaman.test",
        "status": "Open",
        "custom_status_x": "Open",
        "resume_attachment": "/files/cv-recette.pdf",
        "job_title": "HR-OPN-2025-0012",
    }).insert(ignore_permissions=True)
    _note("Notifications candidat", "Job Applicant", d.name, "Rôles Talent Acquisition", "New")


def _webinaire():
    d = frappe.get_doc({
        "doctype": "Amoaman Application",
        "full_name": "Participant Recette Webinaire",
        "email": "participant-recette@amoaman.test",
        "program": PROGRAMME_WEBINAIRE,
    }).insert(ignore_permissions=True)
    _note("Inscription confirmée - Webinaire", "Amoaman Application", d.name, "doc.email", "New")


def _mutations_anniversaires():
    """Pose temporairement un anniversaire et une ancienneté « aujourd'hui ». """
    # Jour/mois = aujourd'hui, année passée (sinon l'anniversaire est ignoré).
    _muter("Employee", EMPLOYE_PRINCIPAL, "date_of_birth", f"1990-{today()[5:7]}-{today()[8:10]}")
    _muter("Employee", EMPLOYE_ANCIENNETE, "date_of_joining", f"2020-{today()[5:7]}-{today()[8:10]}")


# --- Annulation -------------------------------------------------------------

def restaurer():
    """Supprime les documents de recette et restaure les dates anniversaire/ancienneté."""
    chemin = frappe.get_site_path(FICHIER_JOURNAL)
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except (OSError, ValueError):
        donnees = {"journal": [], "mutations": []}

    # Restaurer d'abord les dates mutées (origine None → NULL).
    for doctype, nom, champ, origine in donnees.get("mutations", []):
        try:
            frappe.db.set_value(doctype, nom, champ, origine)
            print(f"  ↺ {doctype} {nom}.{champ} → {origine}")
        except Exception:
            pass

    # Supprimer les documents créés (dans l'ordre inverse pour les dépendances).
    vus = set()
    for e in reversed(donnees.get("journal", [])):
        if e["doctype"] == "Fiscal Year":  # référencé ailleurs ; conservé
            continue
        if (e["doctype"], e["document"]) in vus:
            continue
        vus.add((e["doctype"], e["document"]))
        try:
            if frappe.db.exists(e["doctype"], e["document"]):
                doc = frappe.get_doc(e["doctype"], e["document"])
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc(e["doctype"], e["document"], ignore_permissions=True, force=True)
                print(f"  ✕ {e['doctype']} {e['document']} supprimé")
        except Exception as exc:
            print(f"  ! {e['doctype']} {e['document']} : {exc}")

    frappe.db.commit()
    print("Annulation terminée (le backup --with-files reste la référence).")
