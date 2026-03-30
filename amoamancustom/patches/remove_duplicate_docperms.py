import frappe


def execute():
	"""
	Supprime les doublons dans la table DocPerm (Autorisations) pour chaque DocType.

	Erreur ciblée :
	    "Only one rule allowed with the same Role, Level and If Owner"

	Un doublon est défini par le triplet (role, permlevel, if_owner) identique
	sur plusieurs lignes du même DocType.
	La première occurrence (idx le plus bas) est conservée ; les suivantes sont supprimées.

	Un backup --with-files est effectué avant toute modification.
	"""
	_run_backup()
	_remove_duplicate_doc_perms()


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

def _run_backup():
	from frappe.utils.backups import new_backup

	site = frappe.local.site
	frappe.logger().info(f"[remove_duplicate_docperms] Backup du site '{site}' en cours...")

	odb = new_backup(ignore_files=False, force=True)

	frappe.logger().info(
		f"[remove_duplicate_docperms] Backup terminé — DB : {odb.backup_path_db}"
	)


# ---------------------------------------------------------------------------
# Suppression des doublons
# ---------------------------------------------------------------------------

def _remove_duplicate_doc_perms():
	# Récupère tous les DocTypes ayant au moins une ligne DocPerm
	doctypes = frappe.db.sql(
		"""
		SELECT DISTINCT parent
		FROM `tabDocPerm`
		WHERE parenttype = 'DocType'
		ORDER BY parent
		""",
		as_dict=True,
	)

	total_removed = 0

	for row in doctypes:
		removed = _deduplicate_perms_for_doctype(row.parent)
		total_removed += removed

	frappe.db.commit()

	frappe.logger().info(
		f"[remove_duplicate_docperms] Patch terminé — {total_removed} doublon(s) supprimé(s) "
		f"sur {len(doctypes)} DocType(s) traité(s)."
	)


def _deduplicate_perms_for_doctype(doctype_name):
	"""
	Supprime les lignes DocPerm en doublon pour un DocType donné.
	Retourne le nombre de lignes supprimées.
	"""
	perms = frappe.db.get_all(
		"DocPerm",
		filters={"parent": doctype_name, "parenttype": "DocType"},
		fields=["name", "role", "permlevel", "if_owner"],
		order_by="idx asc",
	)

	if len(perms) <= 1:
		return 0

	seen = set()
	to_delete = []

	for perm in perms:
		key = (
			(perm.role or "").strip(),
			int(perm.permlevel or 0),
			int(perm.if_owner or 0),
		)
		if key in seen:
			to_delete.append(perm.name)
		else:
			seen.add(key)

	if not to_delete:
		return 0

	# Suppression directe en base (DocPerm est une child table gérée en SQL)
	frappe.db.delete("DocPerm", {"name": ("in", to_delete)})

	frappe.logger().info(
		f"[remove_duplicate_docperms] {doctype_name} : {len(to_delete)} doublon(s) supprimé(s) "
		f"({to_delete})"
	)

	return len(to_delete)
