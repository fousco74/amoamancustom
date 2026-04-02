(function patchNotifications() {
	if (!frappe?.ui?.Notifications?.prototype?.make_tab_view) {
		return setTimeout(patchNotifications, 50);
	}

	const proto = frappe.ui.Notifications.prototype;
	if (proto._amoaman_patched) return;
	proto._amoaman_patched = true;

	// ── CSS badge (injecté une seule fois) ──────────────────────────────────
	if (!document.getElementById("amoaman-notif-badge-style")) {
		const style = document.createElement("style");
		style.id = "amoaman-notif-badge-style";
		style.textContent = `
			.sidebar-notification .sidebar-item-icon { position: relative; }
			.notif-count-badge {
				position: absolute;
				top: 1px; right: 1px;
				background: #e74c3c;
				color: #fff;
				font-size: 10px;
				font-weight: 700;
				min-width: 16px;
				height: 16px;
				border-radius: 8px;
				line-height: 16px;
				text-align: center;
				padding: 0 3px;
				pointer-events: none;
				box-sizing: border-box;
			}
		`;
		document.head.appendChild(style);
	}

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

			// Chargement initial — surcharge make() pour mettre à jour le badge dès le départ
			make() {
				super.make();
				// super.make() déclenche get_notifications_list en interne ;
				// on attend que dropdown_items soit rempli puis on met à jour le badge
				this.get_notifications_list(this.max_length).then((r) => {
					if (!r.message) return;
					_update_badge((r.message.notification_logs || []).length);
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
					_update_badge(this.dropdown_items.length);
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
		_update_badge(0);
		// Marquer comme lu côté serveur
		frappe.call({
			method: "frappe.desk.doctype.notification_log.notification_log.mark_all_as_read",
		});
	};

	// ── Badge helpers ────────────────────────────────────────────────────────
	function _update_badge(count) {
		const $icon = $(".sidebar-notification .sidebar-item-icon");
		$icon.find(".notif-count-badge").remove();
		if (count > 0) {
			$icon.append(
				`<span class="notif-count-badge">${count > 99 ? "99+" : count}</span>`
			);
		}
	}
})();
