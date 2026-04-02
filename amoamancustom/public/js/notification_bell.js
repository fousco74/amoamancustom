(function patchNotifications() {
	if (!frappe?.ui?.Notifications?.prototype?.make_tab_view) {
		return setTimeout(patchNotifications, 50);
	}

	const proto = frappe.ui.Notifications.prototype;
	if (proto._amoaman_patched) return;
	proto._amoaman_patched = true;

	const _origMakeTabView = proto.make_tab_view;

	proto.make_tab_view = function (item) {
		if (item.id !== "notifications") {
			return _origMakeTabView.call(this, item);
		}

		const OrigView = item.view;

		class AmoamanNotificationsView extends OrigView {

			// Charge uniquement les notifs non lues (read=0)
			get_notifications_list(limit) {
				return frappe.call({
					method: "amoamancustom.overrides.notification_log.get_notification_logs",
					args: { limit: limit },
					type: "GET",
					cache: false,
				});
			}

			// Appelé lors d'une nouvelle notif en temps réel
			update_dropdown() {
				this._refresh_bell();
			}

			// Au clic : marquer lu puis rafraîchir la cloche (ignoré pour Administrator)
			mark_as_read(docname, $el) {
				if (frappe.session.user === "Administrator") return;
				frappe.call({
					method: "frappe.desk.doctype.notification_log.notification_log.mark_as_read",
					args: { docname: docname },
				}).then(() => {
					this._refresh_bell();
				});
			}

			// Recharge et réaffiche la liste des notifs non lues
			_refresh_bell() {
				this.get_notifications_list(this.max_length).then((r) => {
					if (!r.message) return;
					this.dropdown_items = r.message.notification_logs;
					frappe.update_user_info(r.message.user_info);
					this.container.empty();
					this.render_notifications_dropdown();
				});
			}
		}

		item.view = AmoamanNotificationsView;
		_origMakeTabView.call(this, item);
		item.view = OrigView;
	};

	// Bouton "Tout marquer comme lu" → vide la cloche immédiatement (ignoré pour Administrator)
	proto.mark_all_as_read = function (e) {
		e.stopImmediatePropagation();
		if (frappe.session.user === "Administrator") return;
		// Suppression immédiate du DOM
		if (this.tabs?.notifications) {
			this.tabs.notifications.dropdown_items = [];
			this.tabs.notifications.container.empty();
			this.tabs.notifications.render_notifications_dropdown();
		}
		// Marquer comme lu côté serveur
		frappe.call({
			method: "frappe.desk.doctype.notification_log.notification_log.mark_all_as_read",
		});
	};
})();
