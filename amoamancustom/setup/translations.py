# apps/amoamancustom/amoamancustom/setup/translations.py
"""
Pose en base les traductions françaises que la surcharge de template ne couvre
pas à elle seule — ici, le mail natif « connexion par lien » de Frappe.

Le sujet du mail vient de frappe/www/login.py : `subject = _("Login To {0}")`.
Le corps du template standard passe par `_("Click on the button to log in to {0}")`
et consorts. Ces quatre chaînes ont un `msgstr` vide dans apps/frappe/locale/fr.po
et ne sont traduites dans aucun `.mo` ni CSV d'app : le mail part en anglais.

On ne touche pas à apps/frappe. On écrit des enregistrements `Translation`, qui
ont priorité sur toutes les traductions d'app (frappe/translate.py charge la
base en dernier, donc par-dessus les CSV et les .mo). C'est la même couche que
celle qu'utilise l'écran « Traductions » du Desk.

Doublon volontaire avec amoamancustom/translations/fr.csv : le CSV couvre les
installations futures ; les enregistrements en base s'appliquent immédiatement,
sans recompilation de .mo, et restent robustes à `bench update`.

Idempotent : `installer()` met à jour la traduction si elle existe déjà, la crée
sinon. Rejoué à chaque `bench migrate` via after_migrate.
"""

import frappe

# source -> traduction française. `contexte` reste vide : ces chaînes sont
# enveloppées dans _() sans contexte dans le code de Frappe.
TRADUCTIONS = [
    ("Login To {0}", "Connexion à {0}"),
    ("Log In To {0}", "Se connecter à {0}"),
    ("Click on the button to log in to {0}", "Cliquez sur le bouton pour vous connecter à {0}"),
    ("The link will expire in {0} minutes", "Ce lien expire dans {0} minutes"),
]


def installer():
    """Point d'entrée appelé par `after_migrate`. Idempotent."""
    if not frappe.db.exists("DocType", "Translation"):
        return

    for source, cible in TRADUCTIONS:
        poser_traduction(source, cible)


def poser_traduction(source: str, cible: str) -> bool:
    """Crée ou met à jour la traduction française de `source`. Retourne True si créée."""
    nom = frappe.db.exists(
        "Translation",
        {"source_text": source, "language": "fr"},
    )

    if nom:
        if frappe.db.get_value("Translation", nom, "translated_text") != cible:
            frappe.db.set_value("Translation", nom, "translated_text", cible)
        return False

    doc = frappe.new_doc("Translation")
    doc.language = "fr"
    doc.source_text = source
    doc.translated_text = cible
    doc.insert(ignore_permissions=True)
    return True


def etat():
    """Affiche l'état des traductions du mail de connexion par lien.

        bench --site <site> execute amoamancustom.setup.translations.etat
    """
    for source, cible in TRADUCTIONS:
        nom = frappe.db.exists("Translation", {"source_text": source, "language": "fr"})
        if not nom:
            print(f"ABSENT     {source!r}")
            continue
        en_base = frappe.db.get_value("Translation", nom, "translated_text")
        etiquette = "OK" if en_base == cible else "DIVERGENT"
        print(f"{etiquette:<10} {source!r} -> {en_base!r}")
