frappe.ui.form.on('Project', {
	onload(frm) {

        
        if(frm.doc.sales_order){

            frappe.call({
                method : "amoamancustom.api.get_table_detail",
                args : { doctype : "Sales Order", name : frm.doc.sales_order},
                callback: function (r){
                    if(r.message){
                       
                        let data = r.message
                        let quotation = data.items[0].prevdoc_docname
                            
                        if(quotation){
                            frappe.call({
                                method : "amoamancustom.api.get_table_detail",
                                args : { doctype : "Quotation", name : quotation},
                                callback: function (r){
                                    if(r.message){
                                        let quotation_data = r.message
                                        frm.set_value("expected_start_date", quotation_data.custom_période_du)
                                        frm.set_value("expected_end_date", quotation_data.custom_au)
                                    }
                                }
                            })
                        }

                    }
                }
            })
        }
    },
});