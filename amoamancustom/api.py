import frappe
from frappe import _
from frappe.utils import add_months, getdate, get_first_day, get_last_day, nowdate
from frappe.utils.data import flt
import requests
from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError
from urllib.parse import urlencode


# =============================================================================
# Helpers API externe (prives)
# =============================================================================

def _handle_http_error(exc: requests.HTTPError, url: str) -> None:
    """Traduit les codes HTTP d'erreur externes en frappe.throw lisible."""
    status = exc.response.status_code if exc.response is not None else 0
    try:
        body   = exc.response.json()
        detail = body.get("message") or body.get("error") or body.get("detail") or str(body)
    except Exception:
        detail = exc.response.text if exc.response is not None else str(exc)

    frappe.log_error(f"HTTP {status} - {url}\n{detail}", "External API")

    messages = {
        400: _("Requete invalide envoyee a l'API externe (400) : {0}").format(detail),
        401: _("Non authentifie - verifiez vos credentials API (401)."),
        403: _("Acces refuse par l'API externe (403)."),
        404: _("Ressource introuvable sur l'API externe (404)."),
        422: _("Donnees rejetees par l'API externe (422) : {0}").format(detail),
        429: _("Limite de requetes atteinte (429). Reessayez plus tard."),
        500: _("Erreur interne de l'API externe (500)."),
    }
    frappe.throw(messages.get(status, _("Erreur HTTP {0} : {1}").format(status, detail)))


def _build_headers(token: str = None, api_key: str = None, extra: dict = None) -> dict:
    """Construit les headers HTTP communs pour une API externe."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if api_key:
        headers["X-API-Key"] = api_key
    if extra:
        headers.update(extra)
    return headers


# =============================================================================
# Utilitaires HTTP generiques (whitelisted)
# =============================================================================

@frappe.whitelist()
def external_get(url: str, params: dict | str = None, headers: dict | str = None, timeout: int = 10) -> dict:
    """Requete GET vers une API externe. Retourne le JSON parse."""
    params  = frappe.parse_json(params)  if isinstance(params,  str) else (params  or {})
    headers = frappe.parse_json(headers) if isinstance(headers, str) else (headers or {})
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Timeout:
        frappe.log_error(f"Timeout GET {url}", "External API")
        frappe.throw(_("L'API externe n'a pas repondu dans les delais (GET {0})").format(url))
    except RequestsConnectionError:
        frappe.log_error(f"ConnectionError GET {url}", "External API")
        frappe.throw(_("Impossible de joindre l'API externe : {0}").format(url))
    except requests.HTTPError as e:
        _handle_http_error(e, url)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"external_get: {url}")
        frappe.throw(_("Erreur inattendue lors de l'appel API externe."))


@frappe.whitelist()
def external_post(url: str, payload: dict | str = None, headers: dict | str = None, timeout: int = 15) -> dict:
    """Requete POST vers une API externe."""
    payload = frappe.parse_json(payload) if isinstance(payload, str) else (payload or {})
    headers = frappe.parse_json(headers) if isinstance(headers, str) else (headers or {})
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Timeout:
        frappe.log_error(f"Timeout POST {url}", "External API")
        frappe.throw(_("Timeout lors du POST vers {0}").format(url))
    except RequestsConnectionError:
        frappe.log_error(f"ConnectionError POST {url}", "External API")
        frappe.throw(_("Impossible de joindre : {0}").format(url))
    except requests.HTTPError as e:
        _handle_http_error(e, url)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"external_post: {url}")
        frappe.throw(_("Erreur inattendue lors du POST API externe."))


@frappe.whitelist()
def external_put(url: str, payload: dict | str = None, headers: dict | str = None, timeout: int = 15) -> dict:
    """Requete PUT vers une API externe."""
    payload = frappe.parse_json(payload) if isinstance(payload, str) else (payload or {})
    headers = frappe.parse_json(headers) if isinstance(headers, str) else (headers or {})
    try:
        resp = requests.put(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Timeout:
        frappe.log_error(f"Timeout PUT {url}", "External API")
        frappe.throw(_("Timeout lors du PUT vers {0}").format(url))
    except requests.HTTPError as e:
        _handle_http_error(e, url)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"external_put: {url}")
        frappe.throw(_("Erreur inattendue lors du PUT API externe."))


@frappe.whitelist()
def external_delete(url: str, headers: dict | str = None, timeout: int = 10) -> dict:
    """Requete DELETE vers une API externe."""
    headers = frappe.parse_json(headers) if isinstance(headers, str) else (headers or {})
    try:
        resp = requests.delete(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json() if resp.content else {"status": "deleted"}
    except Timeout:
        frappe.log_error(f"Timeout DELETE {url}", "External API")
        frappe.throw(_("Timeout lors du DELETE vers {0}").format(url))
    except requests.HTTPError as e:
        _handle_http_error(e, url)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"external_delete: {url}")
        frappe.throw(_("Erreur inattendue lors du DELETE API externe."))


# =============================================================================
# LinkedIn
# =============================================================================

def _get_linkedin_settings():
    """Retourne le document LinkedIn Settings (Single)."""
    settings = frappe.get_single("LinkedIn Settings")
    if not settings.base_url:
        frappe.throw(
            _("LinkedIn Settings non configure. Renseignez la Base URL."),
            frappe.ValidationError,
        )
    return settings


_LINKEDIN_CACHE_KEY = "amoamancustom:linkedin_posts"
_LINKEDIN_CACHE_TTL = 86400  # 24 heures

# La Posts API versionnee (format AAAAMM) exige un header LinkedIn-Version valable
# ~12 mois puis "sunset" (au-dela : 426 Upgrade Required). On ne code donc AUCUNE
# version en dur : elle est calculee depuis la date et auto-corrigee sur 426, puis
# memorisee en Redis. Un champ Settings `rest_api_version` permet de forcer une valeur.
_LINKEDIN_VERSION_CACHE_KEY = "amoamancustom:linkedin_api_version"
_LINKEDIN_VERSION_CACHE_TTL = 30 * 86400  # 30 jours


def _li_default_version() -> str:
    """Version AAAAMM dynamique : mois courant - 1 (marge : la version du mois
    courant n'est parfois pas encore publiee cote LinkedIn)."""
    from frappe.utils import now_datetime, add_to_date
    return add_to_date(now_datetime(), months=-1).strftime("%Y%m")


def _li_prev_month(v: str) -> str:
    """'202606' -> '202605' (recule d'un mois, gere le passage d'annee)."""
    from datetime import date
    from frappe.utils import add_to_date
    d = date(int(v[:4]), int(v[4:6]), 1)
    return add_to_date(d, months=-1).strftime("%Y%m")


def _li_resolve_version() -> str:
    """Version a utiliser, par priorite :
    1) version auto-corrigee memorisee en Redis ;
    2) override manuel du champ Settings `rest_api_version` (si renseigne) ;
    3) defaut dynamique `_li_default_version()`."""
    good = frappe.cache().get_value(_LINKEDIN_VERSION_CACHE_KEY)
    if good:
        return good
    # Lecture defensive : si le champ n'existe pas encore (code deploye avant
    # `bench migrate`), get_single_value leve -> on retombe sur le defaut dynamique.
    try:
        override = (frappe.db.get_single_value("LinkedIn Settings", "rest_api_version") or "").strip()
    except Exception:
        override = ""
    return override or _li_default_version()


def _li_rest_base(base_url: str) -> str:
    """Derive l'URL de base /rest a partir de la Base URL configuree."""
    from urllib.parse import urlparse
    p = urlparse(base_url or "https://api.linkedin.com/v2")
    return f"{p.scheme}://{p.netloc}/rest"


def _li_headers(token: str) -> dict:
    """Headers requis par la Posts API LinkedIn (versionnee)."""
    return {
        "Authorization":             f"Bearer {token}",
        "LinkedIn-Version":          _li_resolve_version(),
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _li_get_posts(url: str, params: dict, token: str) -> dict:
    """GET /rest/posts avec auto-correction de version sur 426.

    Essaie d'abord la version resolue (fast-path via cache/override/defaut) ;
    sur 426 on purge la version memorisee, on repart du defaut dynamique et on
    recule mois par mois (max 14, ce qui couvre toute la fenetre valide de 12 mois)
    jusqu'a une reponse non-426. La version gagnante est memorisee en Redis (30 j),
    ce qui evite tout walk-back aux appels suivants."""
    def _call(v: str):
        headers = {
            "Authorization":             f"Bearer {token}",
            "LinkedIn-Version":          v,
            "X-Restli-Protocol-Version": "2.0.0",
        }
        return requests.get(url, params=params, headers=headers, timeout=15)

    v = _li_resolve_version()
    resp = _call(v)
    if resp.status_code == 426:
        # La version memorisee/override est perimee : on la purge et on repart
        # du defaut dynamique, puis on remonte le temps jusqu'a une version valide.
        frappe.cache().delete_value(_LINKEDIN_VERSION_CACHE_KEY)
        v = _li_default_version()
        for _ in range(14):
            resp = _call(v)
            if resp.status_code != 426:
                break
            v = _li_prev_month(v)

    resp.raise_for_status()
    frappe.cache().set_value(_LINKEDIN_VERSION_CACHE_KEY, v,
                             expires_in_sec=_LINKEDIN_VERSION_CACHE_TTL)
    return resp.json()


def _li_clean_text(text: str) -> str:
    """Normalise le texte d'un post : markup LinkedIn, unicode stylise, echappements."""
    import re, unicodedata
    if not text:
        return ""
    # Markup hashtag / mention : {hashtag|\#|Tag}, {mention|...}
    text = re.sub(r"\{hashtag\|\\#\|[^}]*\}", "", text)
    text = re.sub(r"\{mention\|[^}]*\}", "", text)
    # Caracteres "mathematiques" stylises (gras / italique) -> ASCII
    text = unicodedata.normalize("NFKC", text)
    # Echappements LinkedIn : \@  \(  \)  \#  \- ...
    text = re.sub(r"\\([\\@()\[\]{}|*~_#\-!.])", r"\1", text)
    # URLs + espaces superflus
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _li_resolve_image(urn: str, token: str) -> str | None:
    """urn:li:image:... -> downloadUrl affichable (ou None)."""
    from urllib.parse import quote
    try:
        r = requests.get(
            f"https://api.linkedin.com/rest/images/{quote(urn, safe='')}",
            headers=_li_headers(token), timeout=10,
        )
        if r.ok:
            return r.json().get("downloadUrl")
    except Exception:
        pass
    return None


def _li_resolve_video_thumb(urn: str, token: str) -> str | None:
    """urn:li:video:... -> URL de la vignette (ou None)."""
    from urllib.parse import quote
    try:
        r = requests.get(
            f"https://api.linkedin.com/rest/videos/{quote(urn, safe='')}",
            headers=_li_headers(token), timeout=10,
        )
        if r.ok:
            thumb = r.json().get("thumbnail")
            if thumb and str(thumb).startswith("urn:li:image:"):
                return _li_resolve_image(thumb, token)
            return thumb
    except Exception:
        pass
    return None


def _li_resolve_media(content: dict, token: str, resolve_reference: bool = True) -> dict:
    """Normalise le bloc `content` d'un post -> {media_type, image, images, title}."""
    out = {"media_type": "none", "image": None, "images": [], "title": None, "doc_urn": None}
    if not content:
        return out

    # Media simple (image / document / video)
    media = content.get("media")
    if media and media.get("id"):
        urn = media["id"]
        out["title"] = media.get("title")
        if urn.startswith("urn:li:image:"):
            out["media_type"] = "image"
            out["image"]      = _li_resolve_image(urn, token)
        elif urn.startswith("urn:li:document:"):
            out["media_type"] = "document"   # PDF / carrousel : vignette generee a la demande
            out["doc_urn"]    = urn
        elif urn.startswith("urn:li:video:"):
            out["media_type"] = "video"
            out["image"]      = _li_resolve_video_thumb(urn, token)
        return out

    # Multi-images (on ne resout que la 1re pour la perf)
    multi = content.get("multiImage")
    if multi and multi.get("images"):
        urns  = [im.get("id") for im in multi["images"] if im.get("id")]
        first = _li_resolve_image(urns[0], token) if urns else None
        out["media_type"] = "images"
        out["image"]      = first
        out["images"]     = [first] if first else []
        return out

    # Article / lien externe
    article = content.get("article")
    if article:
        out["media_type"] = "article"
        out["title"]      = article.get("title")
        thumb = article.get("thumbnail")
        if thumb:
            out["image"] = (_li_resolve_image(thumb, token)
                            if str(thumb).startswith("urn:li:image:") else thumb)
        return out

    # Repartage : on affiche l'apercu du media du post d'origine
    ref = content.get("reference")
    if ref and resolve_reference:
        from urllib.parse import quote
        ref_urn = ref.get("id") if isinstance(ref, dict) else (ref if isinstance(ref, str) else None)
        if ref_urn and ref_urn.startswith("urn:li:"):
            try:
                rr = requests.get(
                    f"https://api.linkedin.com/rest/posts/{quote(ref_urn, safe='')}",
                    headers=_li_headers(token), timeout=10,
                )
                if rr.ok:
                    inner = _li_resolve_media(rr.json().get("content"), token, resolve_reference=False)
                    if inner["media_type"] != "none":
                        return inner
            except Exception:
                pass
        out["media_type"] = "reshare"
        return out

    # Sondage (pas de media)
    if content.get("poll"):
        out["media_type"] = "poll"
        return out

    return out


@frappe.whitelist(allow_guest=True)
def get_linkedln_post(limit: int = None, org_id: str = None) -> dict:
    """
    Recupere les posts d'une organisation LinkedIn via la Posts API (/rest/posts).
    Retourne une liste normalisee (text / created_time / post_url / media_type / image / images / title).

    Les parametres par defaut sont lus depuis LinkedIn Settings.
    Les resultats sont mis en cache Redis (24h). En cas d'indisponibilite
    reseau, le cache precedent est retourne plutot qu'une liste vide.

    Structure retournee par element :
        post.text.text                                         → texte
        post.created.time                                      → timestamp ms
        post.activity                                          → "urn:li:activity:..." → URL du post
        post.content.contentEntities[0].thumbnails[0].resolvedUrl → image URL

    Appel JS :
        const r = await frappe.call({
            method: "amoamancustom.api.get_linkedln_post"
        });
        console.log(r.message.elements);
    """
    try:
        settings = _get_linkedin_settings()

        # Servir depuis le cache Redis si disponible (evite les appels repetes / 429)
        cached = frappe.cache().get_value(_LINKEDIN_CACHE_KEY)
        if cached:
            return cached

        token = settings.get_valid_token()
        resolved_org_id = org_id or settings.org_id or "70907752"
        resolved_limit  = min(int(limit or settings.default_limit or 6), 50)

        url = f"{_li_rest_base(settings.base_url)}/posts"
        params = {
            "q":      "author",
            "author": f"urn:li:organization:{resolved_org_id}",
            "count":  resolved_limit,
            "sortBy": "LAST_MODIFIED",
        }
        try:
            raw = _li_get_posts(url, params, token)
        except Exception as e:
            frappe.log_error(str(e), "LinkedIn feed")
            cached = frappe.cache().get_value(_LINKEDIN_CACHE_KEY)
            return cached or {"elements": []}

        elements = []
        for post in raw.get("elements", []):
            if post.get("lifecycleState") != "PUBLISHED":
                continue
            media = _li_resolve_media(post.get("content"), token)
            elements.append({
                "text":         _li_clean_text(post.get("commentary", "")),
                "created_time": post.get("createdAt") or post.get("publishedAt"),
                "post_url":     f"https://www.linkedin.com/feed/update/{post.get('id')}",
                "media_type":   media["media_type"],
                "image":        media["image"],
                "images":       media["images"],
                "title":        media["title"],
                "doc_urn":      media["doc_urn"],
            })

        data = {"elements": elements}
        if elements:
            frappe.cache().set_value(_LINKEDIN_CACHE_KEY, data, expires_in_sec=_LINKEDIN_CACHE_TTL)
        return data
    except Exception as e:
        frappe.log_error(str(e), "LinkedIn feed")
        cached = frappe.cache().get_value(_LINKEDIN_CACHE_KEY)
        return cached or {"elements": []}


@frappe.whitelist()
def linkedin_oauth_init() -> dict:
    """
    Genere l'URL d'autorisation LinkedIn OAuth2 et un state CSRF.
    Le front-end ouvre cette URL dans un popup.

    Prerequis dans LinkedIn Settings : client_id renseigne.
    Redirect URI a enregistrer dans le LinkedIn Developer Portal :
        https://{votre-site}/linkedin-oauth-callback
    """
    import secrets
    settings = _get_linkedin_settings()

    if not settings.client_id:
        frappe.throw(_("Client ID manquant dans LinkedIn Settings."), frappe.ValidationError)

    state = secrets.token_urlsafe(32)
    frappe.cache().set_value(f"linkedin_oauth_state:{state}", True, expires_in_sec=300)

    redirect_uri = frappe.utils.get_url("/linkedin-oauth-callback")

    auth_url = "https://www.linkedin.com/oauth/v2/authorization?" + urlencode({
        "response_type": "code",
        "client_id":     settings.client_id,
        "redirect_uri":  redirect_uri,
        "scope":         "r_organization_social",
        "state":         state,
    })

    return {"auth_url": auth_url, "redirect_uri": redirect_uri}


@frappe.whitelist()
def refresh_linkedin_cache() -> dict:
    """
    Force le rafraichissement du cache LinkedIn (appel manuel ou scheduler).
    Pre-genere aussi les vignettes des documents (PDF) pour que le site les
    serve depuis un cache chaud des le premier affichage.
    """
    frappe.cache().delete_value(_LINKEDIN_CACHE_KEY)
    data = get_linkedln_post()
    try:
        _li_warm_doc_cache(data.get("elements", []))
    except Exception as e:
        frappe.log_error(str(e), "LinkedIn doc prewarm")
    return data


def _li_cache_dir() -> str:
    """Dossier de cache disque des medias LinkedIn (cree si absent)."""
    import os
    cache_dir = frappe.get_site_path("public", "files", "linkedin_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _li_atomic_write(path: str, content: bytes) -> None:
    """
    Ecrit `content` dans `path` de maniere atomique (fichier temporaire + rename).
    Evite qu'une requete concurrente lise un fichier a moitie ecrit (vignette cassee).
    """
    import os, tempfile
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        os.replace(tmp, path)   # rename atomique sur le meme filesystem
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _li_doc_cache_path(urn: str) -> str:
    """Chemin de cache de la vignette d'un document (PDF)."""
    import os, hashlib
    return os.path.join(_li_cache_dir(), f"doc_{hashlib.md5(urn.encode()).hexdigest()}.jpg")


def _li_render_doc_thumbnail(urn: str, token: str) -> bytes | None:
    """
    Telecharge le PDF d'un document LinkedIn et rend sa 1re page en JPEG.
    Retourne les octets JPEG, ou None si indisponible. Leve en cas d'erreur reseau.
    """
    import os, tempfile, subprocess
    from urllib.parse import quote

    r = requests.get(
        f"https://api.linkedin.com/rest/documents/{quote(urn, safe='')}",
        headers=_li_headers(token), timeout=15,
    )
    r.raise_for_status()
    pdf_url = r.json().get("downloadUrl")
    if not pdf_url:
        return None

    pr = requests.get(pdf_url, timeout=20)
    if pr.status_code in (401, 403):
        pr = requests.get(pdf_url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    pr.raise_for_status()

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path   = os.path.join(tmp, "in.pdf")
        out_prefix = os.path.join(tmp, "page")
        with open(pdf_path, "wb") as f:
            f.write(pr.content)
        subprocess.run(
            ["pdftoppm", "-jpeg", "-singlefile", "-f", "1", "-l", "1",
             "-scale-to", "1000", pdf_path, out_prefix],
            check=True, timeout=30,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        out_jpg = out_prefix + ".jpg"
        if not os.path.exists(out_jpg):
            return None
        with open(out_jpg, "rb") as f:
            return f.read()


def _li_warm_doc_cache(elements: list) -> None:
    """
    Pre-genere les vignettes des posts 'document' (appele par refresh_linkedin_cache).
    Best-effort : une erreur sur un document n'interrompt pas les autres.
    """
    import os
    docs = [e.get("doc_urn") for e in elements
            if e.get("media_type") == "document" and e.get("doc_urn")]
    if not docs:
        return
    token = _get_linkedin_settings().get_valid_token()
    for urn in docs:
        path = _li_doc_cache_path(urn)
        if os.path.exists(path):
            continue
        try:
            content = _li_render_doc_thumbnail(urn, token)
            if content:
                _li_atomic_write(path, content)
        except Exception as e:
            frappe.log_error(str(e), "LinkedIn doc prewarm")


@frappe.whitelist(allow_guest=True)
def linkedin_img_proxy(url: str):
    """
    Proxy une image LinkedIn CDN avec le Bearer token du serveur.
    Cache disque local dans sites/{site}/public/files/linkedin_cache/.
    Si le fichier est deja en cache, il est servi directement sans appel reseau.
    """
    import re, hashlib, os
    if not re.match(r'^https://[\w.-]*\.licdn\.com/', url):
        frappe.local.response.http_status_code = 403
        return

    url_hash  = hashlib.md5(url.encode()).hexdigest()
    cached_file = os.path.join(_li_cache_dir(), f"li_{url_hash}.jpg")

    # Servir depuis le cache disque si disponible
    if os.path.exists(cached_file):
        with open(cached_file, "rb") as f:
            content = f.read()
        frappe.local.response.update({
            "type":         "binary",
            "filecontent":  content,
            "content_type": "image/jpeg",
            "filename":     "li.jpg",
        })
        return

    try:
        settings = _get_linkedin_settings()
        token    = settings.get_valid_token()
        headers  = _build_headers(token=token)
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        # Sauvegarder sur disque (ecriture atomique) pour les prochaines requetes
        _li_atomic_write(cached_file, resp.content)

        frappe.local.response.update({
            "type":         "binary",
            "filecontent":  resp.content,
            "content_type": resp.headers.get("Content-Type", "image/jpeg"),
            "filename":     "li.jpg",
        })
    except Exception as e:
        frappe.log_error(str(e), "LinkedIn img proxy")
        frappe.local.response.http_status_code = 502


@frappe.whitelist(allow_guest=True)
def linkedin_doc_preview(urn: str):
    """
    Genere une vignette (1re page) d'un document LinkedIn (PDF) -> image JPEG.

    Resout l'URL du PDF via /rest/documents/{urn}, telecharge le PDF, et rend
    sa premiere page en JPEG avec poppler (pdftoppm). Le resultat est mis en
    cache sur disque (linkedin_cache/doc_{hash}.jpg) et servi directement ensuite.
    """
    import re, os

    if not re.match(r"^urn:li:document:[A-Za-z0-9_-]+$", urn or ""):
        frappe.local.response.http_status_code = 400
        return

    def _serve(content: bytes):
        frappe.local.response.update({
            "type": "binary", "filecontent": content,
            "content_type": "image/jpeg", "filename": "doc.jpg",
        })

    cached_file = _li_doc_cache_path(urn)

    # Servir depuis le cache disque si disponible (cas nominal apres pre-generation)
    if os.path.exists(cached_file):
        with open(cached_file, "rb") as f:
            _serve(f.read())
        return

    # Sinon : generer a la demande, mettre en cache (ecriture atomique), servir
    try:
        token   = _get_linkedin_settings().get_valid_token()
        content = _li_render_doc_thumbnail(urn, token)
        if not content:
            frappe.local.response.http_status_code = 404
            return
        _li_atomic_write(cached_file, content)
        _serve(content)
    except Exception as e:
        frappe.log_error(str(e), "LinkedIn doc preview")
        frappe.local.response.http_status_code = 502


# =============================================================================
# DocType helpers
# =============================================================================



# Repli si RH Leave Settings.paid_leave_type n'est pas renseigne.
DEFAULT_PAID_LEAVE_TYPE = "Congés Payés"

# Nombre de mois par sous-periode selon la frequence d'acquisition (earned leave).
_FREQUENCY_STEP_MONTHS = {"Monthly": 1, "Quarterly": 3, "Half-Yearly": 6, "Yearly": 12}


def get_paid_leave_type():
    """Type de conge paye utilise pour le solde et l'indemnite de conge.

    Configurable via le Single « RH Leave Settings » (champ paid_leave_type),
    avec repli sur DEFAULT_PAID_LEAVE_TYPE. Source de verite unique : evite de
    coder le nom du type de conge en dur dans plusieurs fichiers.

    On ne lit le champ que s'il existe reellement (has_field) : le code
    fonctionne donc aussi tant que la migration exposant le champ n'a pas tourne.
    """
    try:
        meta = frappe.get_meta("RH Leave Settings")
    except Exception:
        return DEFAULT_PAID_LEAVE_TYPE

    if meta.has_field("paid_leave_type"):
        value = frappe.db.get_single_value("RH Leave Settings", "paid_leave_type")
        if value:
            return value
    return DEFAULT_PAID_LEAVE_TYPE


def _get_accrued_leave_balance(employee, leave_type, on_date):
    """Solde de conges *acquis* a `on_date`, recalcule periode par periode.

    Pourquoi ne pas simplement sommer le grand livre : pour un conge « earned
    leave » (acquisition periodique, ex. 2,4 j/mois), ERPNext peut retro-allouer
    plusieurs mois d'un seul bloc — typiquement au moment ou la Leave Policy est
    affectee — en datant ce bloc d'une seule journee. Une somme des Leave Ledger
    Entry a une date passee compte alors la totalite du bloc, alors que seuls les
    mois reellement ecoules devraient l'etre (un bulletin de mars affichait 40,8
    au lieu de 36). L'indemnite de conge du solde de tout compte valant
    custom_leave_balance * moy_brut_imp / 30, l'ecart se propage directement.

    On reconstruit donc l'acquisition sous-periode par sous-periode a partir du
    bareme reel : `annual_allocation` de la Leave Policy divise par la frequence,
    via la fonction HRMS get_monthly_earned_leave (qui applique aussi l'arrondi
    et le prorata du mois d'embauche). Passer annual_allocation de 28,8 a 26,4
    donne donc automatiquement 2,2 j/mois au lieu de 2,4.

    Formule par allocation couvrant la date :
        solde = report (unused_leaves, deja net) + acquis(debut_periode -> on_date)
              - conges pris(debut_periode -> on_date)
    ou `acquis` = somme des sous-periodes dont la FIN est atteinte a `on_date`
    (l'acquisition a lieu en fin de sous-periode), plafonnee a annual_allocation.

    Retourne None si aucune allocation « earned + policy » ne couvre `on_date` :
    l'appelant retombe alors sur le calcul HRMS standard.
    """
    from hrms.hr.doctype.leave_application.leave_application import get_leaves_for_period
    from hrms.hr.utils import (
        get_annual_allocation_from_policy,
        get_monthly_earned_leave,
        get_sub_period_start_and_end,
    )

    leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)
    if not leave_type_doc.is_earned_leave:
        return None

    frequency = leave_type_doc.earned_leave_frequency
    step = _FREQUENCY_STEP_MONTHS.get(frequency)
    if not step:
        return None

    allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "docstatus": 1,
            "from_date": ("<=", on_date),
            "to_date": (">=", on_date),
            "leave_policy": ["is", "set"],
        },
        fields=["name", "from_date", "to_date", "unused_leaves", "leave_policy"],
    )
    if not allocations:
        return None

    doj = frappe.db.get_value("Employee", employee, "date_of_joining")
    total = 0.0
    for alloc in allocations:
        annual = flt(get_annual_allocation_from_policy(alloc, leave_type_doc))

        earned = 0.0
        sp_start, sp_end = get_sub_period_start_and_end(getdate(alloc.from_date), frequency)
        while sp_end <= on_date and sp_start <= getdate(alloc.to_date):
            earned += get_monthly_earned_leave(
                doj, annual, frequency, leave_type_doc.rounding, sp_start, sp_end
            )
            nxt = add_months(sp_start, step)
            sp_start, sp_end = get_sub_period_start_and_end(getdate(nxt), frequency)
        earned = min(earned, annual)

        opening = flt(alloc.unused_leaves) + earned
        # get_leaves_for_period renvoie un nombre NEGATIF pour les conges pris
        # (convention HRMS) -> on l'additionne pour retrancher les jours consommes.
        taken = get_leaves_for_period(employee, leave_type, alloc.from_date, on_date)
        total += opening + taken

    return flt(total, 2)


@frappe.whitelist()
def get_leave_balance(employee, leave_type=None, date=None):
    """Solde de conges d'un employe, pour un type de conge, a une date donnee.

    - leave_type non fourni -> resolu via get_paid_leave_type() (configurable).
    - date non fournie      -> aujourd'hui.
    - Pour un conge « earned leave », l'acquisition est recalculee periode par
      periode (_get_accrued_leave_balance) afin que le solde a une date passee
      reflete uniquement les mois reellement ecoules.
    - Repli sur le calcul standard HRMS get_leave_balance_on pour les types non
      « earned », en l'absence d'allocation liee a une policy, ou en cas d'erreur.

    La signature reste compatible avec l'appel client historique
    get_leave_balance(employee) / (employee, leave_type).
    """
    if not employee:
        frappe.throw(_("Employé requis pour calculer le solde de congés."))

    if not leave_type:
        leave_type = get_paid_leave_type()

    on_date = getdate(date) if date else getdate(nowdate())

    try:
        accrued = _get_accrued_leave_balance(employee, leave_type, on_date)
        if accrued is not None:
            return accrued
    except Exception:
        frappe.log_error(frappe.get_traceback(), "ACCRUED_LEAVE_BALANCE_ERROR")

    from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

    return flt(get_leave_balance_on(employee, leave_type, on_date) or 0)


@frappe.whitelist()
def get_table_detail(doctype, name):
    return frappe.get_doc(doctype, name)


def _get_salary_structure_for(employee: str, as_on) -> str | None:
    """Retourne la Salary Structure affectee a la date donnee."""
    as_on = getdate(as_on)
    rows = frappe.get_all(
        "Salary Structure Assignment",
        filters={
            "employee":  employee,
            "from_date": ("<=", as_on),
            "docstatus": 1,
        },
        fields=["salary_structure", "from_date"],
        order_by="from_date desc",
        limit=1,
    )
    return rows[0]["salary_structure"] if rows else None


@frappe.whitelist()
def get_paid_leave_days(employee: str, start_date: str, end_date: str,
                        leave_type: str = "Conges payes", debug: int = 0) -> float:
    """Calcule les jours de conges payes valides et met a jour Employee.custom_validated_paid_leave_days."""
    if not employee or not start_date or not end_date:
        return 0.0

    try:
        sd, ed = getdate(start_date), getdate(end_date)
    except Exception:
        frappe.log_error("get_paid_leave_days: invalid dates", frappe.get_traceback())
        return 0.0

    if sd > ed:
        sd, ed = ed, sd

    period_start = get_first_day(sd)
    period_end   = get_last_day(ed)

    rows = frappe.db.sql("""
        SELECT name, from_date, to_date, total_leave_days
        FROM `tabLeave Application`
        WHERE employee   = %s
          AND leave_type = %s
          AND status     = 'Approved'
          AND docstatus  = 1
          AND from_date <= %s
          AND to_date   >= %s
    """, (employee, leave_type, period_end, period_start), as_dict=True)

    total_days = 0.0
    for r in rows:
        try:
            fd, td = getdate(r.get("from_date")), getdate(r.get("to_date"))
            tld = float(r.get("total_leave_days") or 0)

            overlap_start = fd if fd > period_start else period_start
            overlap_end   = td if td < period_end   else period_end
            if overlap_end < overlap_start:
                continue

            cal_total   = (td - fd).days + 1
            cal_overlap = (overlap_end - overlap_start).days + 1
            if cal_total <= 0 or tld <= 0:
                continue

            total_days += (tld * cal_overlap / cal_total)
        except Exception:
            frappe.log_error("get_paid_leave_days: row processing error", frappe.get_traceback())

    total_days = round(total_days, 2)

    try:
        frappe.db.set_value(
            "Employee",
            employee,
            "custom_validated_paid_leave_days",
            total_days,
            update_modified=False,
        )
    except Exception:
        frappe.log_error("get_paid_leave_days: employee field update failed", frappe.get_traceback())

    return total_days


@frappe.whitelist()
def recalculate_salary_slip(doc):
    """Reconstruit earnings/deductions depuis la Salary Structure."""
    slip_input   = frappe.parse_json(doc)
    salary_slip  = frappe.get_doc(slip_input)

    if salary_slip.employee and salary_slip.start_date and salary_slip.end_date:
        get_paid_leave_days(
            employee=salary_slip.employee,
            start_date=salary_slip.start_date,
            end_date=salary_slip.end_date,
        )

    try:
        frappe.clear_document_cache("Employee", salary_slip.employee)
    except Exception:
        pass

    fresh_paid_days = frappe.db.get_value(
        "Employee", salary_slip.employee, "custom_validated_paid_leave_days"
    ) or 0.0

    try:
        emp = frappe.get_doc("Employee", salary_slip.employee)
        emp.custom_validated_paid_leave_days = fresh_paid_days
        salary_slip.employee_doc = emp
    except Exception:
        pass

    if salary_slip.meta.has_field("custom_validated_paid_leave_days"):
        salary_slip.set("custom_validated_paid_leave_days", flt(fresh_paid_days))

    salary_slip.set("earnings",    [])
    salary_slip.set("deductions",  [])

    if not salary_slip.get("salary_structure"):
        struct = _get_salary_structure_for(salary_slip.employee, salary_slip.start_date)
        if struct:
            salary_slip.salary_structure = struct

    if hasattr(salary_slip, "set_salary_structure_doc"):
        salary_slip.set_salary_structure_doc()
    if hasattr(salary_slip, "pull_sal_struct"):
        salary_slip.pull_sal_struct()

    if hasattr(salary_slip, "calculate_component_amounts"):
        salary_slip.calculate_component_amounts("earnings")
        salary_slip.calculate_component_amounts("deductions")
    elif hasattr(salary_slip, "compute_component_wise_amount"):
        salary_slip.compute_component_wise_amount()
    else:
        salary_slip.gross_pay       = sum(flt(e.amount) for e in salary_slip.get("earnings"))
        salary_slip.total_deduction = sum(flt(d.amount) for d in salary_slip.get("deductions"))

    if hasattr(salary_slip, "calculate_net_pay"):
        salary_slip.calculate_net_pay()
    else:
        salary_slip.net_pay = flt(salary_slip.gross_pay) - flt(salary_slip.total_deduction)

    return {
        "earnings":   [row.as_dict() for row in salary_slip.earnings],
        "deductions": [row.as_dict() for row in salary_slip.deductions],
        "net_pay":    salary_slip.net_pay,
        "paid_days":  fresh_paid_days,
    }


@frappe.whitelist(allow_guest=True)
def create_entry(doctype, data):
    """
    Cree un document Frappe generique.
    Accepte les champs multi-selection envoyes comme liste.
    """
    data = frappe.parse_json(data)

    if not doctype or not isinstance(data, dict):
        frappe.throw(_("Parametres invalides : 'doctype' et 'data' (dict) requis."))

    meta      = frappe.get_meta(doctype)
    field_map = {f.fieldname: f for f in meta.fields}
    doc_data  = {}

    for fieldname, value in data.items():
        if fieldname not in field_map:
            continue
        if isinstance(value, list):
            doc_data[fieldname] = ", ".join(str(v) for v in value)
        else:
            doc_data[fieldname] = value

    doc = frappe.get_doc({"doctype": doctype, **doc_data})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "name":    doc.name,
        "doctype": doc.doctype,
        "message": _("{0} cree avec succes").format(doctype),
    }
