# apps/amoamancustom/amoamancustom/recette/declencher.py
"""
Déclenche tous les mails de recette créés par `donnees.generer()`, en local.

    bench --site <site> execute amoamancustom.recette.declencher.declencher

Deux familles de mails :
1. Les notifications (doctype `Notification`) — déclenchées via
   `evaluate_alert(doc, nom, evenement)`, exactement le chemin emprunté par Frappe
   à l'insertion/soumission/au changement de valeur/au rappel quotidien.
2. Les rappels custom (schedulers d'amoamancustom) — appelés directement.

Politique d'envoi : on n'utilise PAS `flush()` (qui enverrait *toute* la file
d'emails partagée du site, y compris d'éventuels mails légitimes en attente, ni ne
vide-t-on la file). On mémorise les mails déjà en attente avant de déclencher, puis
on n'envoie QUE ceux nouvellement créés par ce run. Ainsi chaque mail de recette
part vers Mailpit (SMTP localhost:1025) sans toucher au reste.
"""

import json

import frappe
from frappe.email.doctype.notification.notification import evaluate_alert

FICHIER_JOURNAL = "private/backups/journal_recette.json"


def _charger_journal():
    with open(frappe.get_site_path(FICHIER_JOURNAL), "r", encoding="utf-8") as f:
        return json.load(f)


def _emails_en_attente():
    """Noms des Email Queue encore à envoyer (avant déclenchement)."""
    return set(
        frappe.get_all(
            "Email Queue",
            filters={"status": ["in", ["Not Sent", "Partially Sent"]]},
            pluck="name",
        )
    )


def _envoyer_uniquement_les_nouveaux(avant):
    """Envoie uniquement les Email Queue apparus après `avant` (nos mails de recette)."""
    nouveaux = sorted(
        frappe.get_all(
            "Email Queue",
            filters={"status": ["in", ["Not Sent", "Partially Sent"]]},
            pluck="name",
        )
    )
    cibles = [n for n in nouveaux if n not in avant]
    if not cibles:
        print("  Aucun nouveau mail à envoyer.")
        return

    print(f"  → {len(cibles)} mail(s) à envoyer (sur {len(nouveaux)} en file).")
    for nom in cibles:
        try:
            frappe.get_doc("Email Queue", nom).send()
            print(f"    ✓ {nom} envoyé")
        except Exception as exc:
            print(f"    ✗ {nom} : {type(exc).__name__}: {str(exc).splitlines()[0][:100]}")


def declencher():
    """Déclenche notifications + rappels custom, n'envoie que les nouveaux, imprime le bilan."""
    donnees = _charger_journal()
    resultats = []
    avant = _emails_en_attente()
    print(f"  File déjà en attente avant le run : {len(avant)} mail(s) (laissés intacts).")

    print("\n=== 1. Notifications (doctype Notification) ===")
    for e in donnees["journal"]:
        nom = e["notification"]
        doctype = e["doctype"]
        doc_nom = e["document"]
        evenement = e["evenement"]

        if not frappe.db.exists(doctype, doc_nom):
            print(f"  [ABSENT ] {nom} ({doctype} {doc_nom} introuvable)")
            resultats.append((nom, "ABSENT"))
            continue

        doc = frappe.get_doc(doctype, doc_nom)

        # Pour les « Value Change », poser la valeur cible qui déclenche la condition.
        if evenement == "Value Change" and e.get("champ_declencheur"):
            setattr(doc, e["champ_declencheur"], e["valeur_declencheur"])

        try:
            evaluate_alert(doc, nom, evenement)
            print(f"  [OK     ] {nom:<38} → {e['destinataire_attendu']}")
            resultats.append((nom, "OK"))
        except Exception as exc:
            print(f"  [ERREUR ] {nom:<38} {type(exc).__name__}: {str(exc).splitlines()[0][:100]}")
            resultats.append((nom, f"ERREUR {type(exc).__name__}"))

    print("\n=== 2. Rappels custom (schedulers amoamancustom) ===")
    schedulers = [
        ("Rappel anniversaire", "amoamancustom.schedulers.hr_reminders.envoyer_rappels_anniversaire", None),
        ("Rappel anniversaire professionnel", "amoamancustom.schedulers.hr_reminders.envoyer_rappels_anniversaire_pro", None),
        ("Rappel jours fériés (hebdo)", "amoamancustom.schedulers.hr_reminders.envoyer_rappels_feries_hebdo", None),
        ("Rappel présence (jour forcé 23)", "amoamancustom.schedulers.attendance_reminder.send_attendance_reminder_continuous", {"jour_force": 23}),
        ("Récap fin de contrat (RH)", "amoamancustom.schedulers.contract_expiry.send_contract_expiry_notifications", None),
    ]

    for libelle, chemin, kwargs in schedulers:
        try:
            methode = frappe.get_attr(chemin)
            methode(**(kwargs or {}))
            print(f"  [OK     ] {libelle}")
            resultats.append((libelle, "OK"))
        except Exception as exc:
            print(f"  [ERREUR ] {libelle:<40} {type(exc).__name__}: {str(exc).splitlines()[0][:100]}")
            resultats.append((libelle, f"ERREUR {type(exc).__name__}"))

    print("\n=== 3. Envoi des nouveaux mails (→ Mailpit) ===")
    _envoyer_uniquement_les_nouveaux(avant)

    print("\n=== Bilan ===")
    ok = sum(1 for _, s in resultats if s == "OK")
    print(f"  {ok}/{len(resultats)} déclenchements sans erreur.")
    print("  Consultez Mailpit : http://localhost:8025  (onglet par destinataire)")
    return resultats
