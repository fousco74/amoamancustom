import frappe


@frappe.whitelist()
def get_notification_logs(limit: int = 20):
	"""Retourne uniquement les notifications NON lues pour l'utilisateur courant."""
	notification_logs = frappe.db.get_list(
		"Notification Log",
		filters={"read": 0},
		fields=["*"],
		limit=limit,
		order_by="creation desc",
	)

	users = list({log.from_user for log in notification_logs if log.from_user})
	user_info = frappe._dict()
	for user in users:
		frappe.utils.add_user_info(user, user_info)

	return {"notification_logs": notification_logs, "user_info": user_info}
