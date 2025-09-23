frappe.ui.form.on('Quotation', {
	onload(frm) {

        
        if(frm.doc.opportunity){

            frappe.call({
                method : "amoamancustom.api.get_table_detail",
                args : { doctype : "Opportunity", name : frm.doc.opportunity},
                callback: function (r){
                    if(r.message){
                        let data = r.message
                        frm.set_value("title", data.title);
                        frm.set_value("custom_période_du", data.custom_date_de_démarrage)
                        frm.set_value("custom_au", data.expected_closing)
                    }
                }
            })
        }
    },
});