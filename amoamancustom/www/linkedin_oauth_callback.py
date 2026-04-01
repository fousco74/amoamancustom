"""
Callback OAuth2 LinkedIn.
URL : https://{site}/linkedin-oauth-callback

LinkedIn redirige ici apres autorisation avec ?code=...&state=...
Ce script echange le code contre les tokens et les sauvegarde dans LinkedIn Settings.
"""

import requests
import frappe
from frappe.utils import now_datetime, add_to_date

no_cache = 1


def get_context(context):
    code  = frappe.request.args.get("code")
    state = frappe.request.args.get("state")
    error = frappe.request.args.get("error")

    if error:
        context.success = False
        context.message = f"LinkedIn a refusé l'accès : {frappe.request.args.get('error_description', error)}"
        return

    # Valider le state (protection CSRF)
    cache_key = f"linkedin_oauth_state:{state}"
    if not state or not frappe.cache().get_value(cache_key):
        context.success = False
        context.message = "Requête invalide ou expirée (state mismatch). Réessayez depuis LinkedIn Settings."
        return
    frappe.cache().delete_value(cache_key)

    # Echanger le code contre les tokens
    try:
        settings     = frappe.get_single("LinkedIn Settings")
        redirect_uri = frappe.utils.get_url("/linkedin-oauth-callback")

        resp = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type":    "authorization_code",
                "code":          code,
                "redirect_uri":  redirect_uri,
                "client_id":     settings.client_id,
                "client_secret": settings.get_password("client_secret"),
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        frappe.log_error(str(e), "LinkedIn OAuth callback")
        context.success = False
        context.message = f"Erreur lors de l'échange du code : {e}"
        return

    access_token  = data.get("access_token")
    refresh_token = data.get("refresh_token")
    expires_in    = data.get("expires_in", 0)

    if not access_token:
        context.success = False
        context.message = "LinkedIn n'a pas retourné de access_token."
        return

    expiry = add_to_date(now_datetime(), seconds=int(expires_in)) if expires_in else None

    update = {"access_token": access_token, "token_expiry": expiry}
    if refresh_token:
        update["refresh_token"] = refresh_token

    frappe.db.set_value("LinkedIn Settings", "LinkedIn Settings", update)
    frappe.db.commit()

    context.success = True
    context.message = "Connexion LinkedIn réussie ! Les tokens ont été sauvegardés."
