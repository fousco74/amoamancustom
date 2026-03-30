frappe.ui.form.on('Loan', {

  async loan_product(frm) {

    const avance_sur_salaire = await frappe.db.get_single_value(
      'Loan Settings',
      'avance_sur_salaire'
    );

    
    if (frm.doc.loan_product === avance_sur_salaire) {



      if (frm.doc.loan_amount) {
        await frm.set_value("monthly_repayment_amount", frm.doc.loan_amount);
        await frm.set_df_property("monthly_repayment_amount", "read_only", true);

      }

    } 
},
async loan_amount(frm){
    const avance_sur_salaire = await frappe.db.get_single_value('Loan Settings', 'avance_sur_salaire');
    if ( frm.doc.loan_product && (frm.doc.loan_product === avance_sur_salaire)) {



        await frm.set_value("monthly_repayment_amount", frm.doc.loan_amount);
        await frm.set_df_property("monthly_repayment_amount", "read_only", true);


    } 

}
});