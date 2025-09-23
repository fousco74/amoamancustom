frappe.ui.form.on('Sales Order', {
	onload(frm) {

        
        if(frm.doc.items[0].prevdoc_docname){

            frappe.call({
                method : "amoamancustom.api.get_table_detail",
                args : { doctype : "Quotation", name : frm.doc.items[0].prevdoc_docname},
                callback: function (r){
                    if(r.message){
                        let data = r.message
                        frm.set_value("delivery_date", data.custom_au);
                        frm.set_value("custom_ca_commandé_ht", data.total)
                    }
                }
            })
        }
    },
});