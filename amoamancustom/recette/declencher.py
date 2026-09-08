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

# Destinataires de la recette : au lieu d'arroser tous les membres des rôles
# (HR Manager 4, employés 20, présence 23…), on limite l'envoi à ce petit
# échantillon de comptes de test, pour que chaque type de mail soit vérifiable
# dans Mailpit sans bruit. Modifiez librement cette liste (2-3 adresses).
DESTINATAIRES_TEST = [
    "skouakou@amoaman.com",
    "damoakon@amoaman.com",
    "eanoma@amoaman.com",
]


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


def _limiter_destinataires(nom):
    """Réécrit la table enfant `recipients` d'un Email Queue vers DESTINATAIRES_TEST.

    On ne limite que les mails « collectifs » (rôle / liste > 3 destinataires) :
    un mail déjà individuel (rappel de présence ou de jour férié adressé à un
    employé précis) part tel quel, sans être gonflé en 3 copies.
    """
    doc = frappe.get_doc("Email Queue", nom)
    if len(doc.recipients) <= len(DESTINATAIRES_TEST):
        return
    doc.recipients = []
    for addr in DESTINATAIRES_TEST:
        doc.append("recipients", {"recipient": addr, "status": "Not Sent"})
    doc.save(ignore_permissions=True)


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
            _limiter_destinataires(nom)
            frappe.get_doc("Email Queue", nom).send()
            print(f"    ✓ {nom} envoyé → {', '.join(DESTINATAIRES_TEST)}")
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


def retester_problemes():
    """Re-test ciblé des 3 types qui n'émettaient pas de mail en recette.

    1. « Récap fin de contrat (RH) » — code corrigé : il lit désormais le doctype
       `Contract` (même source que la notification « Contrat proche expiration »)
       au lieu de `Employee.contract_end_date` (toujours vide). Rien à préparer.
    2. « Rappel jours fériés (hebdo) » — code correct mais aucune donnée dans la
       fenêtre : on injecte un jour férié témoin (non hebdomadaire) à J+3.
    3. « Rappel présence » — correct mais dédupliqué : on purge le journal du jour.
    """
    avant = _emails_en_attente()

    # 2. Jour férié témoin (idempotent) dans la fenêtre des 7 jours.
    date_test = frappe.utils.add_days(frappe.utils.today(), 3)
    if not frappe.db.exists(
        "Holiday", {"parent": "Liste des jours fériés", "holiday_date": date_test}
    ):
        hl = frappe.get_doc("Holiday List", "Liste des jours fériés")
        hl.append(
            "holidays",
            {"description": "Jour férié de recette (à supprimer)", "holiday_date": date_test, "weekly_off": 0},
        )
        hl.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"  + jour férié témoin : {date_test}")

    # 3. Purge du journal de déduplication du jour (présence).
    frappe.db.sql(
        "DELETE FROM `tabAttendance Reminder Log` WHERE status=%s AND sent_date=%s",
        ("Sent", frappe.utils.today()),
    )
    frappe.db.commit()
    print("  ↺ journal présence (jour) purgé")

    print("\n=== Relance des 3 schedulers ===")
    schedulers = [
        ("Récap fin de contrat (RH)", "amoamancustom.schedulers.contract_expiry.send_contract_expiry_notifications", None),
        ("Rappel jours fériés (hebdo)", "amoamancustom.schedulers.hr_reminders.envoyer_rappels_feries_hebdo", None),
        ("Rappel présence (jour forcé 23)", "amoamancustom.schedulers.attendance_reminder.send_attendance_reminder_continuous", {"jour_force": 23}),
    ]
    for libelle, chemin, kwargs in schedulers:
        try:
            frappe.get_attr(chemin)(**(kwargs or {}))
            print(f"  [OK     ] {libelle}")
        except Exception as exc:
            print(f"  [ERREUR ] {libelle:<40} {type(exc).__name__}: {str(exc).splitlines()[0][:100]}")

    print("\n=== Envoi des nouveaux mails (→ Mailpit) ===")
    _envoyer_uniquement_les_nouveaux(avant)
