# apps/amoamancustom/amoamancustom/recette/diagnostic.py
"""Diagnostics ciblés sur les notifications (sans envoyer de mail)."""
import json

import frappe
from frappe.email.doctype.notification.notification import get_context

NOTIFICATIONS = [
    "Entretien de départ programmé", "Formation programmée", "Partagez votre avis sur la formation",
    "Prime de fidélisation à venir", "Demande de matériel reçue", "Contrat proche expiration",
    "Demande de congés - en attente DG MAIL", "Demande de congés - en attente RH MAIL",
    "Validation Demande de congés", "Notifications candidat", "Contact Notification",
    "New HD ticket", "Nouvel exercice fiscal", "Inscription confirmée - Webinaire",
]


def _config(notif):
    d = frappe.get_doc("Notification", notif)
    print(f"\n### {notif}  (event={d.event}, channel={d.channel}, cond_type={d.condition_type})")
    if d.condition:
        print(f"    condition: {d.condition[:140]}")
    if d.value_changed:
        print(f"    value_changed: {d.value_changed}")
    if d.date_changed:
        print(f"    date_changed: {d.date_changed}  (days_in_advance={d.days_in_advance})")
    if not d.recipients:
        print("    recipients: (aucun)")
    for r in d.recipients:
        print(
            f"    recipient: role={r.receiver_by_role!r} field={r.receiver_by_document_field!r} "
            f"cc={r.cc!r} bcc={r.bcc!r} cond={(r.condition or '')[:50]!r}"
        )


def _resoudre(doctype, name, notif):
    doc = frappe.get_doc(doctype, name)
    alert = frappe.get_doc("Notification", notif)
    context = get_context(doc)
    context.update({"alert": alert, "comments": None})
    recips, cc, bcc = alert.get_list_of_recipients(doc, context)
    statut = "OK" if recips else "VIDE (aucun destinataire résolu)"
    print(f"    -> [{doctype} {name}] {statut}  recipients={recips!r} cc={cc!r} bcc={bcc!r}")


def dump_destinataires():
    """Affiche, pour chaque notification, la config exacte des destinataires."""
    for n in NOTIFICATIONS:
        d = frappe.get_doc("Notification", n)
        recips = [
            (r.receiver_by_role or "", r.receiver_by_document_field or "", (r.cc or ""))
            for r in d.recipients
        ]
        print(f"{n}\n    {recips}")


def diagnostiquer():
    print("===== Configurations des 14 notifications =====")
    for n in NOTIFICATIONS:
        _config(n)

    print("\n===== Résolution effective des destinataires (documents de recette) =====")
    journal = json.load(open(frappe.get_site_path("private/backups/journal_recette.json")))
    for e in journal["journal"]:
        if frappe.db.exists(e["doctype"], e["document"]):
            _resoudre(e["doctype"], e["document"], e["notification"])
