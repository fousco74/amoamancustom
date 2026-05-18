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

            get_notifications_list(limit) {
                return frappe.call({
                    method: "amoamancustom.overrides.notification_log.get_notification_logs",
                    args: { limit: limit },
                    type: "GET",
                    cache: false,
                });
            }

            update_dropdown() {
                this._refresh_bell();
            }

            render_notifications_dropdown() {
                super.render_notifications_dropdown();
                _update_notif_badge(this.dropdown_items?.length || 0);
                this._bind_click_mark_read();
            }

            _bind_click_mark_read() {
                this.container.off("click.amoaman_mark");
                this.container.on("click.amoaman_mark", ".notification-item[data-name]", (e) => {
                    const $item = $(e.currentTarget);
                    const docname = $item.data("name");
                    if (!docname) return;

                    $item.remove();
                    this.dropdown_items = (this.dropdown_items || []).filter(n => n.name !== docname);
                    _update_notif_badge(this.dropdown_items.length);

                    frappe.call({
                        method: "frappe.desk.doctype.notification_log.notification_log.mark_as_read",
                        args: { docname: docname },
                    });
                });
            }

            _refresh_bell() {
                this.get_notifications_list(this.max_length).then((r) => {
                    if (!r.message) return;
                    this.dropdown_items = r.message.notification_logs || [];
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

    // Mark all as read
    proto.mark_all_as_read = function (e) {
        e.stopImmediatePropagation();
        if (this.tabs?.notifications) {
            this.tabs.notifications.dropdown_items = [];
            this.tabs.notifications.container.empty();
            this.tabs.notifications.render_notifications_dropdown();
        }
        _update_notif_badge(0);
        frappe.call({
            method: "frappe.desk.doctype.notification_log.notification_log.mark_all_as_read",
        });
    };

    // ==================== SIDEBAR LABEL VISIBILITY ====================
    function handleSidebarLabels() {
        const $sidebar = $('.body-sidebar-container');
        const $labels = $('.sidebar-item-label');
		const $ctrl = $('.sidebar-item-suffix .keyboard-shortcut');

        if ($sidebar.hasClass('expanded')) {
			$labels.removeClass('hidden');
			$ctrl.removeClass('hidden');

        } else {
			$labels.addClass('hidden');
			$ctrl.addClass('hidden');

        }
    }

    // Inject CSS
    if (!document.getElementById("am-notif-badge-css")) {
        const s = document.createElement("style");
        s.id = "am-notif-badge-css";
        s.textContent = `
            .sidebar-notification .sidebar-item-icon { position: relative !important; }
            .body-sidebar .standard-sidebar-item .item-anchor { overflow: visible !important; }
            
            .am-notif-badge {
                position: absolute; top: -4px; right: -2px;
                background: #e74c3c; color: #fff;
                font-size: 10px; font-weight: 700;
                z-index: 9999 !important;
                min-width: 16px; height: 16px;
                border-radius: 8px; line-height: 16px;
                text-align: center; padding: 0 3px;
                pointer-events: none; box-sizing: border-box;
            }
        `;
        document.head.appendChild(s);
    }

    function _update_notif_badge(count) {
        const $iconSidebar = $(".sidebar-notification .sidebar-item-icon");
        const $iconHome = $(".dropdown-notifications .btn-reset");

        $(".am-notif-badge").remove();

        if (count > 0) {
            const text = count > 99 ? "99+" : count;
            $iconSidebar.append(`<span class="am-notif-badge">${text}</span>`);
            $iconHome.append(`<span class="am-notif-badge">${text}</span>`);
        }
    }

    // Initial call + observer pour les changements de sidebar
    $(document).ready(() => {
        handleSidebarLabels();

        // Observer les changements de classe sur le sidebar (recommandé)
        const sidebarObserver = new MutationObserver(handleSidebarLabels);
        const sidebarContainer = document.querySelector('.body-sidebar-container');
        
        if (sidebarContainer) {
            sidebarObserver.observe(sidebarContainer, {
                attributes: true,
                attributeFilter: ['class']
            });
        }

        // Backup : clic sur le toggle
        $(document).on('click', '.sidebar-toggle, .body-sidebar-container', handleSidebarLabels);
    });

})();