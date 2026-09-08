# apps/amoamancustom/amoamancustom/recette/nettoyage.py
"""
Nettoyage de l'état laissé par un `generer()` interrompu (commit avant l'écriture
du journal). Restaure les 3 dates mutées à leur vraie valeur d'origine (relue dans
le backup --with-files du 2026-09-07 23:15) puis supprime les documents de recette
créés. Ne touche ni au SMTP (déjà repointé vers Mailpit), ni aux fichiers.

    bench --site <site> execute amoamancustom.recette.nettoyage.nettoyer
"""

import frappe

# Valeurs d'origine lues dans le backup `20260907_231524` (avant phase 2).
ORIGINAUX = {
    ("Employee", "A7", "relieving_date"): None,
    ("Employee", "A7", "date_of_birth"): "1997-04-24",
    ("Employee", "A21", "date_of_joining"): "2025-06-10",
}

# Documents de recette créés par le `generer()` interrompu.
DOCS = [
    ("Exit Interview", "HR-EXIT-INT-00001"),
    ("Training Result", "HR-TRR-2026-00001"),
    ("Training Event", "Formation recette notification"),   # soumis
    ("Retention Bonus", "HR-RTB-2026-00001"),                # soumis
    ("Material Request", "MAT-MR-2026-00001"),
    ("Fiscal Year", "2027"),
    ("Contract", "CON-2026-00002"),
    ("Leave Application", "HR-LAP-2026-00053"),
    ("HD Ticket", "0109"),
    ("Contact Us", "vbhq77qrd3"),
    ("Job Applicant", "candidat-recette@amoaman.test"),
    ("Amoaman Application", "vbkqb51lpf"),
]


def nettoyer():
    print("=== Restauration des dates mutées ===")
    for (doctype, nom, champ), valeur in ORIGINAUX.items():
        frappe.db.set_value(doctype, nom, champ, valeur)
        print(f"  ↺ {doctype} {nom}.{champ} → {valeur}")

    print("=== Suppression des documents de recette ===")
    for doctype, nom in DOCS:
        if not frappe.db.exists(doctype, nom):
            print(f"  – {doctype} {nom} (absent)")
            continue
        try:
            doc = frappe.get_doc(doctype, nom)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc(doctype, nom, ignore_permissions=True, force=True)
            print(f"  ✕ {doctype} {nom} supprimé")
        except Exception as exc:
            print(f"  ! {doctype} {nom}: {type(exc).__name__}: {str(exc)[:140]}")

    frappe.db.commit()
    print("=== Nettoyage terminé ===")
