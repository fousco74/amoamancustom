frappe.ui.form.on('Loan Application', {

  async loan_product(frm) {

    const avance_sur_salaire = await frappe.db.get_single_value(
      'Loan Settings',
      'avance_sur_salaire'
    );

    const pret = await frappe.db.get_single_value(
      'Loan Settings',
      'prêt'
    );

    if (frm.doc.loan_product === avance_sur_salaire) {

      const option = "Repay Fixed Amount per Period";

      frm.set_df_property("repayment_method", "options", option);

      if (frm.doc.repayment_method !== option) {
        await frm.set_value("repayment_method", option);
      }

    } else if (frm.doc.loan_product === pret) {

      const option = "Repay Over Number of Periods";

      frm.set_df_property("repayment_method", "options", option);

      if (frm.doc.repayment_method !== option) {
        await frm.set_value("repayment_method", option);
      }

    } else {

      // Restore default options
      frm.set_df_property(
        "repayment_method",
        "options",
        "Repay Fixed Amount per Period\nRepay Over Number of Periods"
      );

      frm.set_value("repayment_method", "");
    }

    frm.refresh_field("repayment_method");
  },

  loan_amount(frm) {

    if (frm.doc.loan_amount) {

      frm.set_value("repayment_amount", frm.doc.loan_amount);

      frm.set_df_property("repayment_amount", "read_only", 1);

    } else {

      frm.set_df_property("repayment_amount", "read_only", 0);

    }

  }

});