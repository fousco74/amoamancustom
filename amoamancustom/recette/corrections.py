# apps/amoamancustom/amoamancustom/recette/corrections.py
"""
Correctifs des notifications détectés pendant la recette (sans toucher aux apps
standard : uniquement des enregistrements `Notification`, c'est-à-dire de la donnée).

    bench --site <site> execute amoamancustom.recette.corrections.corriger

1. « Validation Demande de congés » :
   - objet recopié à tort de la notification « en attente DG » : il annonçait
     « En attente de validation DG » alors que le déclencheur est workflow_state
     = « Approuvé ». Corrigé en « Approuvée ».
   - destinataire `receiver_by_document_field = "owner"` → le champ owner contient
     le nom d'utilisateur (pas une adresse) : la résolution est vide. Remplacé par
     le rôle « HR Manager » (le RH est informé de la validation).

2. « Demande de matériel reçue » :
   - même problème `owner`. Remplacé par le rôle « Stock Manager » (l'équipe qui
     réceptionne le matériel).

Ces choix de rôle sont documentés ici et faciles à ajuster dans l'écran
« Notification » si l'intention métier diffère.
"""

import frappe


def _remplacer_destinataire_par_role(notification, role):
    doc = frappe.get_doc("Notification", notification)
    doc.recipients = []
    doc.append("recipients", {"receiver_by_role": role})
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print(f"  ↺ {notification} : destinataire → rôle « {role} »")


def corriger():
    print("=== Correctifs notifications ===")

    # 1. Validation Demande de congés : objet + destinataire
    d = frappe.get_doc("Notification", "Validation Demande de congés")
    ancien = d.subject
    d.subject = "Demande de congé {{ doc.employee_name }} - Approuvée"
    d.save(ignore_permissions=True)
    print(f"  ↺ Validation Demande de congés : sujet\n      « {ancien} » → « {d.subject} »")
    _remplacer_destinataire_par_role("Validation Demande de congés", "HR Manager")

    # 2. Demande de matériel reçue : destinataire
    _remplacer_destinataire_par_role("Demande de matériel reçue", "Stock Manager")

    frappe.db.commit()
    print("=== Correctifs terminés ===")


def corriger_nom_app(nom=None):
    """Le mail « lien de connexion » affichait « Login To Axis » : `app_name` vaut
    « Axis » (valeur de démo ERPNext) côté Website Settings, et « Frappe » côté
    System Settings. On remet le nom de l'entreprise pour que le sujet devienne
    « Connexion à <société> » (la traduction « Login To {0} » → « Connexion à {0} »
    est déjà installée via `setup.translations`). Donnée, pas code standard."""
    nom = nom or frappe.db.get_default("company") or "AMOAMAN & ASSOCIES"

    ws = frappe.get_single("Website Settings")
    ancien_ws = ws.app_name
    ws.app_name = nom
    ws.save(ignore_permissions=True)

    ss = frappe.get_single("System Settings")
    ancien_ss = ss.app_name
    ss.app_name = nom
    ss.save(ignore_permissions=True)

    frappe.db.commit()
    print(f"  ↺ Website Settings.app_name : « {ancien_ws} » → « {nom} »")
    print(f"  ↺ System Settings.app_name  : « {ancien_ss} » → « {nom} »")


def corriger_accents():
    """Répare les accents manquants de la notification « Rappel Jours Feries »
    (fixture importée sans accents) : renomme l'enregistrement et corrige l'objet
    pour que le mail parte avec « Jours fériés à venir ». Idempotent."""
    if frappe.db.exists("Notification", "Rappel Jours Feries"):
        try:
            frappe.rename_doc("Notification", "Rappel Jours Feries", "Rappel Jours Fériés", force=True)
        except Exception as exc:
            print(f"  ! rename ignoré : {type(exc).__name__}: {str(exc)[:120]}")
    if frappe.db.exists("Notification", "Rappel Jours Fériés"):
        frappe.db.set_value("Notification", "Rappel Jours Fériés", "subject", "Jours fériés à venir")
        print("  ↺ « Rappel Jours Fériés » : sujet → « Jours fériés à venir »")
    frappe.db.commit()
