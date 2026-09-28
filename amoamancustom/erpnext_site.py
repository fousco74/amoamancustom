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
	"""Empreinte des fichiers statiques du mini-site, a coller en query string.

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

	# Les images comptent aussi : un logo reexporte sous le meme nom resterait
	# douze heures dans le cache des visiteurs sans cette prise en compte.
	# On lit la date du DOSSIER, pas de chaque fichier : elle change des qu'un
	# fichier y est ajoute, remplace ou supprime, pour le prix d'un seul stat().
	try:
		dernier = max(dernier, int(os.path.getmtime(os.path.join(_PUBLIC, "images", "erpnext"))))
	except OSError:
		pass

	return str(dernier)


def base_context(context, title, description="", active="", page="accueil"):
	"""Applique le contexte commun du mini-site et retourne `context`.

	Appelée par le `get_context` de chaque page de www/erpnext/.
	"""
	# La seconde classe porte le fond de page : chaque cadre Figma a le sien
	# (uni sur l'accueil, degrade plein cadre sur les trois autres).
	context.body_class = f"erpx erpx-page-{page}"
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
# Liste canonique : consommee par la grille de l'accueil, par le carrousel
# « Découvrir d'autres modules » des pages module ET par les cartes detaillees
# de /erpnext/modules. La dupliquer dans les templates ferait diverger les
# affichages a la premiere retouche.
#
# `icon` designe un fichier de templates/includes/erpnext/icons/ ; les glyphes
# proviennent d'Iconify, dont les identifiants sont les noms de calque de la
# maquette (solar:box-bold -> module-stocks.svg, etc.).
#
# `titre` / `precision` : la maquette de /erpnext/modules (4168:426) coupe le
# seul intitule compose en deux lignes de corps different — « Comptabilité » en
# 24px, « ( + Intégration directe FNE ) » en 15px. Les deux morceaux sont donc
# stockes separement ; `libelle()` les recolle pour les tuiles et le footer,
# qui affichent l'intitule complet sur une seule ligne.
#
# `icon_taille` : cote du glyphe EN PIXELS sur la carte de /erpnext/modules.
# La maquette le fait varier de 50 a 65 d'une carte a l'autre (equilibrage
# optique : une usine pleine cadre pese plus lourd qu'une ampoule), alors que
# les titres, eux, restent alignes d'une colonne a l'autre. On reprend donc la
# valeur de chaque carte ; le viewBox de chaque export la porte deja a
# l'identique. Sans effet sur les tuiles, dimensionnees en CSS.
#
# `icon_miroir` : la maquette applique un miroir horizontal a 11 glyphes sur
# 12 (Immos seul y echappe), AUSSI BIEN sur les tuiles de l'accueil que sur
# les cartes du catalogue — verifie en comparant la tuile « Achats » du cadre
# a l'export brut : le chariot y est retourne. C'est vraisemblablement un accident de calque —
# un caddie et une devanture de magasin s'y retrouvent retournes — mais c'est
# ce que rend le cadre Figma, et le champ existe pour que le constat soit
# explicite et se corrige en une ligne si le studio le confirme.
#
# `desc` : releve mot pour mot sur les cartes de la maquette (4168:427 et
# suivants). Sert UNIQUEMENT a /erpnext/modules ; les tuiles n'affichent que
# l'intitule.
#
# L'ORDRE de ce tuple est celui de la grille 4 colonnes de l'ACCUEIL
# (4105:2454) : …, Qualité, RH & Paie, Support, Immos, Points de vente. La page
# catalogue, elle, est sur 3 colonnes et suit ORDRE_PAGE_MODULES.
#
# `route` reste vide tant que le module n'a pas de page dediee : l'appelant
# rabat alors la tuile sur /erpnext/modules plutot que de produire un lien
# mort. Seul Stocks a une page a ce stade.
MODULES = (
	{
		"key": "comptabilite",
		"titre": "Comptabilité",
		"precision": "( + Intégration directe FNE )",
		"desc": "Centralisez vos opérations financières aux normes SYSCOHADA et automatisez"
		" votre conformité FNE et vos états en temps réel.",
		"icon": "module-comptabilite",
		"icon_taille": 60,
		"icon_miroir": True,
		"route": "",
	},
	{
		"key": "achats",
		"titre": "Achats",
		"precision": "",
		"desc": "Digitalisez votre processus d'approvisionnement, maîtrisez vos budgets et"
		" simplifiez les échanges fournisseurs.",
		"icon": "module-achats",
		"icon_taille": 60,
		"icon_miroir": True,
		"route": "",
	},
	{
		"key": "production",
		"titre": "Production",
		"precision": "",
		"desc": "Optimisez vos cycles de fabrication avec un suivi précis de vos fiches de"
		" travail, nomenclatures et ressources.",
		"icon": "module-production",
		"icon_taille": 65,
		"icon_miroir": True,
		"route": "",
	},
	{
		"key": "projets",
		"titre": "Projets",
		"precision": "",
		"desc": "Pilotez la rentabilité, le respect des délais et le suivi des tâches de vos"
		" projets en totale transparence.",
		"icon": "module-projets",
		"icon_taille": 59,
		"icon_miroir": True,
		"route": "",
	},
	{
		"key": "ventes",
		"titre": "Ventes",
		"precision": "",
		"desc": "Accélérez vos cycles commerciaux, du devis à l'encaissement, tout en"
		" automatisant vos règles tarifaires.",
		"icon": "module-ventes",
		"icon_taille": 60,
		"icon_miroir": True,
		"route": "",
	},
	{
		"key": "crm",
		"titre": "CRM",
		"precision": "",
		"desc": "Qualifiez vos prospects, pilotez votre pipeline commercial et transformez"
		" chaque opportunité en vente durable.",
		"icon": "module-crm",
		"icon_taille": 55,
		"icon_miroir": True,
		"route": "",
	},
	{
		"key": "stocks",
		"titre": "Stocks",
		"precision": "",
		"desc": "Gardez une visibilité totale et en temps réel sur vos niveaux de stock,"
		" mouvements et entrepôts.",
		"icon": "module-stocks",
		"icon_taille": 50,
		"icon_miroir": True,
		"route": "/erpnext/modules/stocks",
	},
	{
		"key": "qualite",
		"titre": "Qualité",
		"precision": "",
		"desc": "Garantissez l'excellence de vos produits grâce à des contrôles automatisés,"
		" la traçabilité et la gestion des non-conformités.",
		"icon": "module-qualite",
		"icon_taille": 52,
		"icon_miroir": True,
		"route": "",
	},
	{
		"key": "rh-paie",
		"titre": "RH & Paie",
		"precision": "",
		"desc": "Automatisez la paie, la gestion des absences et le suivi des talents au sein"
		" d'une plateforme moderne.",
		"icon": "module-rh-paie",
		"icon_taille": 65,
		"icon_miroir": True,
		"route": "",
	},
	{
		"key": "support",
		"titre": "Support",
		"precision": "",
		"desc": "Offrez un service client d'exception grâce à la centralisation des tickets,"
		" des SLA et un portail libre-service.",
		"icon": "module-support",
		"icon_taille": 60,
		"icon_miroir": True,
		"route": "",
	},
	{
		"key": "immos",
		"titre": "Immos",
		"precision": "",
		"desc": "Pilotez le cycle de vie complet de vos actifs, du calcul automatisé des"
		" amortissements jusqu'à leur cession.",
		"icon": "module-immos",
		"icon_taille": 56,
		"icon_miroir": False,
		"route": "",
	},
	{
		"key": "points-de-vente",
		"titre": "Points de vente",
		"precision": "",
		"desc": "Enregistrez vos ventes rapidement, gérez vos caisses en direct et"
		" synchronisez votre stock instantanément.",
		"icon": "module-points-de-vente",
		"icon_taille": 59,
		"icon_miroir": True,
		"route": "",
	},
)

# Destination de repli d'un module sans page dediee. Avant l'existence de
# /erpnext/modules, les tuiles pointaient sur l'ancre #modules de l'accueil,
# donc sur la section qu'on venait de cliquer.
PAGE_MODULES = "/erpnext/modules"

# Ordre de la grille 3 colonnes de /erpnext/modules (layer 4167:265). Il DIFFERE
# de l'ordre de MODULES, qui est celui de la grille 4 colonnes de l'accueil
# (4105:2454) : la maquette tient a placer « Immos » en 3e colonne de la 3e
# ligne dans les DEUX cas, ce qu'aucun ordre unique ne peut donner a la fois sur
# 4 et sur 3 colonnes. D'ou une sequence par largeur de grille, et non un
# reclassement de MODULES — qui deplacerait les tuiles de l'accueil.
ORDRE_PAGE_MODULES = (
	"comptabilite",
	"achats",
	"production",
	"projets",
	"ventes",
	"crm",
	"stocks",
	"qualite",
	"immos",
	"rh-paie",
	"support",
	"points-de-vente",
)


def libelle(module):
	"""Intitule complet d'un module, sur une ligne.

	Les intitules ne passent PAS par frappe._() : ce sont des noms d'offre, pas
	des chaines d'interface. Le CSV de traduction de l'app rend « Support » par
	« Assistance/Support », ce qui deformait la tuile par rapport a la maquette.
	Le site est monolingue francais : les libelles sont deja dans la bonne langue.
	"""
	return f"{module['titre']} {module['precision']}".strip() if module["precision"] else module["titre"]


def modules(exclude=""):
	"""Liste des modules prete a etre rendue par erpx_module_tile().

	`exclude` retire un module de la liste — utilise par une page module pour
	ne pas se proposer elle-meme dans « Découvrir d'autres modules ».
	"""
	return [
		{
			"label": libelle(module),
			"titre": module["titre"],
			"precision": module["precision"],
			"icon": module["icon"],
			"icon_miroir": module["icon_miroir"],
			"href": module["route"] or PAGE_MODULES,
		}
		for module in MODULES
		if module["key"] != exclude
	]


def modules_detailles():
	"""Les 12 modules dans l'ordre et avec le contenu des cartes de /erpnext/modules.

	`href` vaut "" quand le module n'a pas de page dediee : la carte est alors
	rendue en <article> et non en <a>, pour ne pas offrir un lien qui ramenerait
	sur la page courante. Meme parti que la colonne « Secteurs » du footer.
	"""
	par_cle = {module["key"]: module for module in MODULES}
	return [
		{
			"titre": par_cle[cle]["titre"],
			"precision": par_cle[cle]["precision"],
			"desc": par_cle[cle]["desc"],
			"icon": par_cle[cle]["icon"],
			"icon_taille": par_cle[cle]["icon_taille"],
			"icon_miroir": par_cle[cle]["icon_miroir"],
			"href": par_cle[cle]["route"],
		}
		for cle in ORDRE_PAGE_MODULES
	]
