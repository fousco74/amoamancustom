# apps/amoamancustom/amoamancustom/recette/emails_auth.py
"""
Déclenche les 3 mails d'authentification (réinitialisation de mot de passe,
bienvenue, lien de connexion) pour 2-3 comptes de test, en local (Mailpit).

    bench --site <site> execute amoamancustom.recette.emails_auth.declencher_auth

Ces mails sont envoyés *par utilisateur* (pas par rôle), donc on boucle sur les
mêmes comptes témoins que `declencher.DESTINATAIRES_TEST`. Ils partent tous vers
Mailpit (SMTP localhost:1025) sans toucher au reste de la file partagée, car les
méthodes natives `_reset_password` / `send_welcome_mail_to_user` / `send_login_link`
appellent `frappe.sendmail(..., now=True)` — envoi immédiat, pas de mise en file
à retardement.
"""

import frappe

DESTINATAIRES_TEST = [
    "skouakou@amoaman.com",
    "damoakon@amoaman.com",
    "eanoma@amoaman.com",
]


def _reglages():
    return {
        "login_with_email_link": frappe.db.get_system_setting("login_with_email_link"),
        "expiry": frappe.db.get_system_setting("login_with_email_link_expiry"),
        "reset_password_template": frappe.db.get_system_setting("reset_password_template"),
        "welcome_email_template": frappe.db.get_system_setting("welcome_email_template"),
        "app_name (website)": frappe.get_website_settings("app_name"),
        "app_name (system)": frappe.db.get_system_setting("app_name"),
        "site_name": frappe.db.get_default("site_name"),
    }


def verifier_francais():
    """Prouve que le sujet du lien de connexion sort en français quand langue = fr
    (le bench CLI tourne par défaut en « en », d'où « Login To … » vu plus haut)."""
    frappe.local.lang = "fr"
    sujet = frappe._("Login To {0}").format("AMOAMAN & ASSOCIES")
    print(f"  lang={frappe.local.lang!r}  →  sujet = « {sujet} »")
    # Preuve de bout en bout : un vrai mail avec la langue forcée à « fr ».
    frappe.get_attr("frappe.www.login.send_login_link")("skouakou@amoaman.com")
    print("  → 1 lien de connexion (lang=fr) envoyé vers Mailpit pour contrôle du sujet.")


def verifier_reglages():
    """Imprime les réglages + les traductions FR du lien de connexion, sans rien envoyer."""
    print("=== Réglages d'authentification ===")
    for k, v in _reglages().items():
        print(f"  {k:<26} = {v!r}")
    print("\n=== Traductions FR (source_text ~ 'Login To %') ===")
    for t in frappe.get_all(
        "Translation",
        filters={"language": "fr", "source_text": ["like", "Login To%"]},
        fields=["source_text", "translated_text"],
    ):
        print(f"  « {t['source_text']} » → « {t['translated_text']} »")


def declencher_auth():
    print("=== Réglages d'authentification ===")
    for k, v in _reglages().items():
        print(f"  {k:<26} = {v!r}")

    print("\n=== Mails d'authentification (3 × 3 comptes) ===")
    for email in DESTINATAIRES_TEST:
        if not frappe.db.exists("User", email):
            print(f"  [ABSENT ] {email} — utilisateur introuvable, ignoré")
            continue
        u = frappe.get_doc("User", email)

        # 1. Réinitialisation de mot de passe (custom_template reset_password_template)
        u._reset_password(send_email=True)
        print(f"  ✓ réinitialisation mot de passe → {email}")

        # 2. Email de bienvenue (custom_template welcome_email_template)
        u.send_welcome_mail_to_user()
        print(f"  ✓ bienvenue                  → {email}")

        # 3. Lien de connexion (template login_with_email_link, surchargé par l'app)
        frappe.get_attr("frappe.www.login.send_login_link")(email)
        print(f"  ✓ lien de connexion          → {email}")

    print("\nConsultez Mailpit : http://localhost:8025")
