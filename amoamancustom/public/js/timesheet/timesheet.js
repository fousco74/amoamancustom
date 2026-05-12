frappe.ui.form.on('Timesheet', {
    employee(frm) {
        if (frm.doc.employee) {
            frappe.call({
                method: "amoamancustom.facturation.doctype.timesheet.timesheet.user_project",
                args: {
                    employee: frm.doc.employee
                },
                callback: function (r) {
                    if (r.message) {

                        // ⚡ Restreindre le champ "parent_project"
                        frm.set_query("parent_project", function () {
                            return {
                                filters: {
                                    name: ["in", r.message.projects]
                                }
                            };
                        });

                        // ⚡ Restreindre le champ "customer"
                        frm.set_query("customer", function () {
                            return {
                                filters: {
                                    name: ["in", r.message.customers]
                                }
                            };
                        });

                           // Appliquer aux lignes existantes — activity_type
                        frm.fields_dict["time_logs"].grid.get_field("activity_type").get_query = function() {
                            return {
                                filters: {
                                    name: ["in", r.message.activity_types]
                                }
                            };
                        };

                           // Appliquer aux lignes existantes — project
                        frm.fields_dict["time_logs"].grid.get_field("project").get_query = function() {
                            return {
                                filters: {
                                    name: ["in", r.message.projects]
                                }
                            };
                        };


                    }
                }
            });
        }
    }
});


function buildMinimalTimesheet(frm) {
  return {
    doctype: 'Timesheet',
    employee: frm.doc.employee || null,
    time_logs: (frm.doc.time_logs || []).map(tl => ({
      doctype: 'Timesheet Detail',
      name: tl.name,
      from_time: tl.from_time,
      to_time: tl.to_time
    }))
  };
}

const recalc_row = frappe.utils.debounce(async function (frm, cdt, cdn) {
  const row = locals[cdt][cdn];
  if (!row || !row.from_time || !row.to_time) return;

  try {
    const minimal = buildMinimalTimesheet(frm);

    const r = await frappe.xcall(
      'amoamancustom.facturation.doctype.timesheet.timesheet.recalc_timesheet_row',
      { timesheet: minimal, row_name: row.name }
    );

    frappe.model.set_value(cdt, cdn, 'custom_days', r.days);
    // billing_hours est utilisé par ERPNext pour les Sales Invoices et les totaux
    frappe.model.set_value(cdt, cdn, 'billing_hours', r.days);

    // en-tête (si le champ existe chez toi)
    if (frm.get_field('custom_total_working_days')) {
      frm.set_value('custom_total_working_days', r.total_days);
    }

  } catch (e) {
    try {
      if (e && e._server_messages) {
        const msgs = JSON.parse(e._server_messages).map(m => {
          try { return JSON.parse(m).message || m; } catch { return m; }
        }).join('<br>');
        frappe.msgprint(msgs);
      } else if (e && e.exc) {
        frappe.msgprint(`<pre>${frappe.utils.escape_html(
          (Array.isArray(e.exc) ? e.exc.join('\n') : e.exc) || ''
        )}</pre>`);
      } else {
        frappe.msgprint(__('Erreur: ') + String(e && (e.message || e.status_text || e.status || 'inconnue')));
      }
    } catch {
      frappe.msgprint(__('Erreur inconnue'));
    }
  }
}, 300);




frappe.ui.form.on('Timesheet Detail', {
    from_time(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); },
    to_time(frm, cdt, cdn)   { recalc_row(frm, cdt, cdn); }
});



