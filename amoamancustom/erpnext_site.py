# apps/amoamancustom/amoamancustom/erpnext_site.py
"""
Contexte commun aux pages du mini-site « Amoaman intégrateur ERPNext ».

Trois réglages sont indispensables et faciles à oublier page par page ; ils sont
donc posés ici une fois pour toutes :

    body_class = "erpx"
        Tous les tokens CSS du mini-site vivent sur `.erpx`
        (public/css/erpnext_site.css) et non sur `:root`, pour ne rien laisser
        fuir vers le site corporate qui a ses propres --blue-*, --pink-*, --text.
        `body_class` est lu par frappe/templates/base.html:57. Sans lui, la page
        s'affiche sans aucun style.

    full_width = 1
        Lu par frappe/templates/web.html : retire la classe .container de
        <main>. C'est la voie prévue par le framework — préférable à un
        `main.container { max-width: none }` en CSS, que fait le site historique.

    no_cache = 1
        Les pages sont assemblées à partir de plusieurs includes ; le cache HTML
        de Frappe (@cache_html) masquerait les modifications en développement.

Le `title` sert au <title> et aux métadonnées Open Graph, `description` au SEO,
et `erpx_active` surligne l'entrée courante dans la navbar.
"""

import os

# Racine des fichiers statiques de l'app, pour l'empreinte de version ci-dessous.
_PUBLIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")


def assets_version():
	"""Empreinte de la CSS et du JS du mini-site, a coller en query string.

	Frappe sert /assets/** avec `Cache-Control: max-age=43200` : sans empreinte, un
	visiteur garde l'ancienne feuille de style pendant douze heures apres une mise
	en production. Les bundles `*.bundle.css` de `bench build` repondent a ce
	besoin par un nom de fichier hache, mais cette app reference ses CSS en direct
	(cf. templates/layout.html:9) ; on garde cette convention et on y ajoute la
	date de modification la plus recente des deux fichiers.

	Retourne "0" si les fichiers sont introuvables : une URL sans empreinte reste
	preferable a une erreur de rendu.
	"""
	dernier = 0

	for chemin in (
		os.path.join(_PUBLIC, "css", "erpnext_site.css"),
		os.path.join(_PUBLIC, "js", "erpnext_site.js"),
	):
		try:
			dernier = max(dernier, int(os.path.getmtime(chemin)))
		except OSError:
			continue

	return str(dernier)


def base_context(context, title, description="", active=""):
	"""Applique le contexte commun du mini-site et retourne `context`.

	Appelée par le `get_context` de chaque page de www/erpnext/.
	"""
	context.body_class = "erpx"
	context.full_width = 1
	context.no_cache = 1
	context.no_breadcrumbs = 1

	context.title = title
	context.erpx_active = active
	context.erpx_assets_v = assets_version()

	if description:
		context.description = description
		context.metatags = {
			"title": title,
			"description": description,
			"og:type": "website",
		}

	return context


# ---------------------------------------------------------------------------
# Les 12 modules mis en avant par le mini-site.
# ---------------------------------------------------------------------------
# Liste canonique : consommee par la grille de l'accueil ET par le carrousel
# « Découvrir d'autres modules » des pages module. La dupliquer dans les
# templates ferait diverger les deux affichages a la premiere retouche.
#
# `icon` designe un fichier de templates/includes/erpnext/icons/ ; les glyphes
# proviennent d'Iconify, dont les identifiants sont les noms de calque de la
# maquette (solar:box-bold -> module-stocks.svg, etc.).
#
# `route` reste vide tant que le module n'a pas de page dediee : le gabarit
# rabat alors la tuile sur l'ancre #modules de l'accueil plutot que de produire
# un lien mort. Seul Stocks a une page a ce stade.
MODULES = (
	{"key": "comptabilite",    "label": "Comptabilité ( + Intégration directe FNE )", "icon": "module-comptabilite",    "route": ""},
	{"key": "achats",          "label": "Achats",                                     "icon": "module-achats",          "route": ""},
	{"key": "production",      "label": "Production",                                 "icon": "module-production",      "route": ""},
	{"key": "projets",         "label": "Projets",                                    "icon": "module-projets",         "route": ""},
	{"key": "ventes",          "label": "Ventes",                                     "icon": "module-ventes",          "route": ""},
	{"key": "crm",             "label": "CRM",                                        "icon": "module-crm",             "route": ""},
	{"key": "stocks",          "label": "Stocks",                                     "icon": "module-stocks",          "route": "/erpnext/modules/stocks"},
	{"key": "qualite",         "label": "Qualité",                                    "icon": "module-qualite",         "route": ""},
	{"key": "rh-paie",         "label": "RH & Paie",                                  "icon": "module-rh-paie",         "route": ""},
	{"key": "support",         "label": "Support",                                    "icon": "module-support",         "route": ""},
	{"key": "immos",           "label": "Immos",                                      "icon": "module-immos",           "route": ""},
	{"key": "points-de-vente", "label": "Points de vente",                            "icon": "module-points-de-vente", "route": ""},
)


def modules(exclude=""):
	"""Liste des modules prete a etre rendue par erpx_module_tile().

	`exclude` retire un module de la liste — utilise par une page module pour
	ne pas se proposer elle-meme dans « Découvrir d'autres modules ».
	"""
	# Les intitules ne passent PAS par frappe._() : ce sont des noms d'offre, pas
	# des chaines d'interface. Le CSV de traduction de l'app rend « Support » par
	# « Assistance/Support », ce qui deformait la tuile par rapport a la maquette.
	# Le site est monolingue francais : les libelles sont deja dans la bonne langue.
	return [
		{
			"label": module["label"],
			"icon": module["icon"],
			"href": module["route"] or "/erpnext#modules",
		}
		for module in MODULES
		if module["key"] != exclude
	]
