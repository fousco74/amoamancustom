// Copyright (c) 2025, KONE Fousseni and contributors
// For license information, please see license.txt

frappe.ui.form.on("Amoaman Event", {
	refresh(frm) {
		if (frm.doc.__islocal) return;

		if (frm.doc.status === "Published" || frm.doc.status === "Draft") {
			frm.add_custom_button(__("Fermer l'événement"), function () {
				frappe.confirm(
					__("Fermer cet événement ? Les inscriptions ne seront plus acceptées."),
					function () {
						frappe.call({
							method: "amoamancustom.amoaman_custom_app.doctype.amoaman_event.amoaman_event.close_event",
							args: { name: frm.doc.name },
							callback() {
								frm.reload_doc();
							},
						});
					}
				);
			}, __("Actions"));
		}

		if (frm.doc.status === "Closed" || frm.doc.status === "Cancelled") {
			frm.add_custom_button(__("Rouvrir l'événement"), function () {
				frappe.confirm(
					__("Rouvrir cet événement ? Les inscriptions seront à nouveau acceptées."),
					function () {
						frappe.call({
							method: "amoamancustom.amoaman_custom_app.doctype.amoaman_event.amoaman_event.open_event",
							args: { name: frm.doc.name },
							callback() {
								frm.reload_doc();
							},
						});
					}
				);
			}, __("Actions"));
		}
	},
});
