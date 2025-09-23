frappe.ui.form.on('Salary Slip', {
  employee: recalc_with_ppl,
  start_date: recalc_with_ppl,
  end_date: recalc_with_ppl
});

function recalc_with_ppl(frm) {
  if (!frm.doc.employee || !frm.doc.start_date || !frm.doc.end_date) return;

  frappe.call({
    method: "amoamancustom.api.recalculate_salary_slip",
    args: { doc: frm.doc },
    freeze: true,
    freeze_message: __("Recalcul des composantes..."),
    callback: function(r) {
      if (!r.message) return;

      frm.set_value('earnings', r.message.earnings || []);
      frm.set_value('deductions', r.message.deductions || []);
      if (r.message.net_pay !== undefined) {
        frm.set_value('net_pay', r.message.net_pay);
      }
      if (frm.fields_dict.custom_validated_paid_leave_days &&
          r.message.paid_days !== undefined) {
        frm.set_value('custom_validated_paid_leave_days', r.message.paid_days);
      }
      frm.refresh_fields(["earnings","deductions","net_pay","custom_validated_paid_leave_days"]);
    }
  });
}
