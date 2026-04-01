import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date, get_datetime

import requests

_LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
# Renouvellement declanche si le token expire dans moins de 24h
_REFRESH_THRESHOLD_HOURS = 24


class LinkedInSettings(Document):

    def validate(self):
        if self.default_limit and (int(self.default_limit) < 1 or int(self.default_limit) > 50):
            frappe.throw(_("Le nombre de posts doit être compris entre 1 et 50."))

        if self.base_url:
            self.base_url = self.base_url.rstrip("/")

    def get_token(self) -> str:
        """Retourne le token, leve une erreur explicite s'il est absent."""
        token = self.get_password("access_token")
        if not token:
            frappe.throw(
                _("Token LinkedIn manquant. Configurez-le dans LinkedIn Settings."),
                frappe.AuthenticationError,
            )
        return token

    def can_auto_refresh(self) -> bool:
        """Retourne True si les credentials OAuth2 sont disponibles pour un refresh auto."""
        return bool(
            self.client_id
            and self.get_password("client_secret")
            and self.get_password("refresh_token")
        )

    def token_needs_refresh(self) -> bool:
        """
        Retourne True si le token est absent ou expire dans moins de _REFRESH_THRESHOLD_HOURS.
        """
        if not self.get_password("access_token"):
            return True
        if not self.token_expiry:
            # Pas de date connue : on tente quand meme un refresh preventif
            return True
        threshold = add_to_date(now_datetime(), hours=_REFRESH_THRESHOLD_HOURS)
        return get_datetime(self.token_expiry) <= threshold

    def refresh_access_token(self) -> str:
        """
        Renouvelle l'access token via le refresh token OAuth2 LinkedIn.
        Met a jour access_token et token_expiry dans le document puis sauvegarde.
        Retourne le nouvel access token.

        Endpoint LinkedIn :
            POST https://www.linkedin.com/oauth/v2/accessToken
            Content-Type: application/x-www-form-urlencoded
            Body: grant_type=refresh_token&refresh_token=...&client_id=...&client_secret=...

        Reponse :
            {
              "access_token": "...",
              "expires_in": 5183944,          # secondes
              "refresh_token": "...",          # nouveau refresh token (si fourni)
              "refresh_token_expires_in": ..., # secondes
              "token_type": "Bearer"
            }
        """
        if not self.can_auto_refresh():
            frappe.throw(
                _("Refresh auto impossible : renseignez Client ID, Client Secret et Refresh Token dans LinkedIn Settings."),
                frappe.ValidationError,
            )

        client_secret = self.get_password("client_secret")
        refresh_token = self.get_password("refresh_token")

        try:
            resp = requests.post(
                _LINKEDIN_TOKEN_URL,
                data={
                    "grant_type":    "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id":     self.client_id,
                    "client_secret": client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
            resp.raise_for_status()
        except requests.HTTPError as e:
            try:
                detail = e.response.json()
            except Exception:
                detail = e.response.text if e.response else str(e)
            frappe.log_error(str(detail), "LinkedIn token refresh")
            frappe.throw(
                _("Echec du renouvellement du token LinkedIn ({0}) : {1}").format(
                    e.response.status_code if e.response else "?", detail
                )
            )
        except Exception as e:
            frappe.log_error(str(e), "LinkedIn token refresh")
            frappe.throw(_("Erreur reseau lors du renouvellement du token LinkedIn."))

        data = resp.json()
        new_token   = data.get("access_token")
        expires_in  = data.get("expires_in", 0)        # secondes
        new_refresh = data.get("refresh_token")         # LinkedIn peut fournir un nouveau

        if not new_token:
            frappe.throw(_("La reponse LinkedIn ne contient pas de access_token."))

        # Mise a jour du document (db_set pour eviter les hooks de validation)
        expiry = add_to_date(now_datetime(), seconds=int(expires_in)) if expires_in else None

        frappe.db.set_value("LinkedIn Settings", "LinkedIn Settings", {
            "access_token":  new_token,
            "token_expiry":  expiry,
        })

        # Mise a jour du refresh token si LinkedIn en fournit un nouveau
        if new_refresh and new_refresh != refresh_token:
            frappe.db.set_value("LinkedIn Settings", "LinkedIn Settings", {
                "refresh_token": new_refresh,
            })

        frappe.db.commit()
        frappe.log_error(
            f"Token renouvele, expire le {expiry}",
            "LinkedIn token refresh OK",
        )
        return new_token

    def get_valid_token(self) -> str:
        """
        Retourne un token valide.
        Si le token est expire (ou proche de l'expiration) et que les credentials
        OAuth2 sont disponibles, un refresh est tente automatiquement.
        """
        if self.token_needs_refresh() and self.can_auto_refresh():
            try:
                return self.refresh_access_token()
            except Exception:
                # Si le refresh echoue, on tente quand meme avec le token existant
                pass
        return self.get_token()
