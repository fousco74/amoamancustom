# apps/amoamancustom/amoamancustom/setup/scheduler.py
"""
Neutralise les rappels RH anglais livrés par HRMS, au profit des nôtres.

Anniversaire, anniversaire professionnel et jours fériés sont les trois seuls
mails RH sans point d'extension : leur contenu est codé en dur dans
hrms/controllers/employee_reminders.py, sans champ Email Template.

On ne touche pas au code de HRMS. On coupe l'enregistrement `Scheduled Job Type`
correspondant, qui est une donnée du site : `sync_jobs` (frappe/migrate.py:162)
matérialise les `scheduler_events` déclarés dans les hooks sous forme
d'enregistrements, et `stopped` est un champ de ces enregistrements. Le passer à
1 est un UPDATE en base — `apps/hrms/` reste inchangé.

On coupe le JOB, pas la case de HR Settings : celle-ci est relue par nos propres
schedulers (amoamancustom/schedulers/hr_reminders.py), de sorte que l'écran RH
garde exactement le comportement qu'il avait avant.

Robustesse : `insert_single_event` (frappe .../scheduled_job_type.py:268) ne
réécrit que `frequency` et `cron_format` sur un job existant — « Maintain
existing values of other fields ». `stopped = 1` survit donc à `bench migrate`
et aux montées de version de HRMS.

Limite connue : `clear_events` supprime tout job dont la méthode n'est plus
déclarée dans les hooks. Si HRMS renomme une de ces méthodes, l'enregistrement
part avec notre `stopped`, un nouveau est créé à 0, et le rappel anglais repart
en doublon des nôtres. D'où le journal d'erreur ci-dessous, qui rend ce cas
visible au lieu de silencieux.
"""

import frappe

# Trois rappels, mais quatre jobs : les jours fériés ont une variante
# hebdomadaire et une mensuelle, HR Settings.frequency choisissant laquelle
# s'exécute réellement.
JOBS_HRMS_A_COUPER = (
	"hrms.controllers.employee_reminders.send_birthday_reminders",
	"hrms.controllers.employee_reminders.send_work_anniversary_reminders",
	"hrms.controllers.employee_reminders.send_reminders_in_advance_weekly",
	"hrms.controllers.employee_reminders.send_reminders_in_advance_monthly",
)


def couper_rappels_hrms():
	"""Point d'entrée appelé par `after_migrate`. Idempotent et auto-réparant.

	Rejoué à chaque migration : si quelqu'un décoche « Stopped » dans l'interface,
	la migration suivante le remet.
	"""
	if not frappe.db.exists("DocType", "Scheduled Job Type"):
		return

	for methode in JOBS_HRMS_A_COUPER:
		nom = frappe.db.exists("Scheduled Job Type", {"method": methode})

		if not nom:
			if "hrms" in frappe.get_installed_apps():
				frappe.log_error(
					title="Rappels RH : job HRMS introuvable",
					message=(
						f"{methode} n'a plus d'enregistrement Scheduled Job Type.\n\n"
						"HRMS l'a probablement renommé lors d'une montée de version. "
						"Vérifier qu'aucun rappel en anglais n'est reparti en doublon "
						"des rappels d'amoamancustom, et mettre à jour "
						"amoamancustom/setup/scheduler.py:JOBS_HRMS_A_COUPER."
					),
				)
			continue

		if not frappe.db.get_value("Scheduled Job Type", nom, "stopped"):
			frappe.db.set_value("Scheduled Job Type", nom, "stopped", 1)


def etat():
	"""Affiche l'état des jobs de rappel, les nôtres et ceux de HRMS.

	    bench --site <site> execute amoamancustom.setup.scheduler.etat
	"""
	lignes = frappe.get_all(
		"Scheduled Job Type",
		filters={"method": ["like", "%reminder%"]},
		fields=["name", "method", "frequency", "stopped"],
		order_by="method",
	)
	lignes += frappe.get_all(
		"Scheduled Job Type",
		filters={"method": ["like", "amoamancustom.schedulers.hr_reminders%"]},
		fields=["name", "method", "frequency", "stopped"],
		order_by="method",
	)

	for l in lignes:
		etiquette = "COUPÉ " if l.stopped else "ACTIF "
		print(f"  {etiquette} {l.frequency:<8} {l.method}")
