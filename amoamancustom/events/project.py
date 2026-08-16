import frappe


def after_insert(doc, method):
	"""Prévient les ressources affectées qu'un projet vient d'être créé.

	Le HTML vit dans amoamancustom/templates/emails/nouveau_projet.html, qui
	étend le gabarit commun _base_mail.html : mise en page, bouton « Ouvrir dans
	ERPNext » et lien d'instance sont partagés avec les autres mails de
	l'application.
	"""
	if not doc.users:
		return

	recipients = sorted({u.user for u in doc.users if u.user})
	if not recipients:
		return

	message = frappe.render_template(
		"amoamancustom/templates/emails/nouveau_projet.html",
		{"projet": doc},
		is_path=True,
	)

	frappe.sendmail(
		recipients=recipients,
		subject=f"Nouveau projet : {doc.project_name}",
		message=message,
		reference_doctype=doc.doctype,
		reference_name=doc.name,
	)
