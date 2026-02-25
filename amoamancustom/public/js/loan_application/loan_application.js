frappe.ui.form.on('Loan Application', {
  async loan_product(frm) {
    // Charger les 2 valeurs de configuration depuis le Single doctype
    const avance_sur_salaire = await frappe.db.get_single_value(
      'Loan Settings',
      'avance_sur_salaire'
    );
    const pret = await frappe.db.get_single_value(
      'Loan Settings',
      'prêt'
    );

    // Restreindre les options de repayment_method selon le produit
    if (frm.doc.loan_product === avance_sur_salaire) {
      const opt = 'Repay Fixed Amount per Period';
      frm.set_df_property('repayment_method', 'options', opt); // 1 seule option
      if (frm.doc.repayment_method !== opt) {
        await frm.set_value('repayment_method', opt);
      }
    } else if (frm.doc.loan_product === pret) {
      const opt = 'Repay Over Number of Periods';
      frm.set_df_property('repayment_method', 'options', opt); // 1 seule option
      if (frm.doc.repayment_method !== opt) {
        await frm.set_value('repayment_method', opt);
      }
    } else {
      // Optionnel : remettre les options par défaut si ce n'est ni avance ni prêt
      // frm.set_df_property('repayment_method', 'options', "Repay Fixed Amount per Period\nRepay Over Number of Periods");
      // await frm.set_value('repayment_method', null);
    }

    frm.refresh_field('repayment_method');
  },
  loan_amount(frm){
    if(frm.doc.loan_amount){
      frm.set_value("repayment_amount", frm.doc.loan_amount);
      frm.set_df_property("repayment_amount", "read_only", true);
    }
  }
});
