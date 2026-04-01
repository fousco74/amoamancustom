frappe.ui.form.on("LinkedIn Settings", {

    refresh(frm) {
        // ── Bouton OAuth2 ────────────────────────────────────────────────
        frm.add_custom_button(__("Autoriser l'accès LinkedIn"), () => {
            if (!frm.doc.client_id) {
                frappe.msgprint({
                    title:   __("Configuration manquante"),
                    message: __("Renseignez d'abord le <b>Client ID</b> et sauvegardez."),
                    indicator: "orange",
                });
                return;
            }

            frappe.call({
                method: "amoamancustom.api.linkedin_oauth_init",
                callback(r) {
                    if (!r.message?.auth_url) return;

                    // Afficher le redirect_uri pour que l'admin puisse le copier si besoin
                    frappe.show_alert({
                        message: __("Redirect URI : {0}", [r.message.redirect_uri]),
                        indicator: "blue",
                    }, 8);

                    const popup = window.open(
                        r.message.auth_url,
                        "linkedin_oauth",
                        "width=620,height=720,left=200,top=100"
                    );

                    if (!popup) {
                        frappe.msgprint(__("Le popup a été bloqué. Autorisez les popups pour ce site."));
                        return;
                    }

                    const handler = (event) => {
                        if (event.data?.type !== "linkedin_oauth") return;
                        window.removeEventListener("message", handler);

                        if (event.data.status === "success") {
                            frappe.show_alert({
                                message:   __("✅ Connexion LinkedIn réussie ! Tokens sauvegardés."),
                                indicator: "green",
                            }, 6);
                            frm.reload_doc();
                        } else {
                            frappe.msgprint({
                                title:     __("Échec OAuth2"),
                                message:   event.data.message || __("Erreur inconnue."),
                                indicator: "red",
                            });
                        }
                    };
                    window.addEventListener("message", handler);
                },
            });
        }, __("OAuth2"));

        // ── Bouton refresh manuel du cache posts ─────────────────────────
        frm.add_custom_button(__("Rafraîchir le cache posts"), () => {
            frappe.call({
                method:  "amoamancustom.api.refresh_linkedin_cache",
                freeze:  true,
                freeze_message: __("Chargement des posts LinkedIn…"),
                callback(r) {
                    const count = r.message?.elements?.length || 0;
                    frappe.show_alert({
                        message:   count
                            ? __("{0} post(s) mis en cache.", [count])
                            : __("Aucun post récupéré (vérifiez le token)."),
                        indicator: count ? "green" : "orange",
                    }, 5);
                },
            });
        }, __("OAuth2"));

        // ── Indicateur expiration token ──────────────────────────────────
        if (frm.doc.token_expiry) {
            const expiry  = frappe.datetime.str_to_obj(frm.doc.token_expiry);
            const diffMs  = expiry - new Date();
            const diffDays = Math.round(diffMs / 86400000);

            if (diffDays <= 0) {
                frm.set_intro(__("⚠️ Le token LinkedIn est <b>expiré</b>. Cliquez sur « Autoriser l'accès LinkedIn »."), "red");
            } else if (diffDays <= 7) {
                frm.set_intro(__("⚠️ Le token expire dans <b>{0} jour(s)</b>.", [diffDays]), "orange");
            } else {
                frm.set_intro(__("✅ Token valide encore <b>{0} jour(s)</b>.", [diffDays]), "blue");
            }
        } else if (!frm.doc.access_token) {
            frm.set_intro(__("Renseignez le Client ID & Client Secret, puis cliquez sur « Autoriser l'accès LinkedIn »."), "orange");
        }
    },
});
