// Copyright (c) 2025, KONE Fousseni and contributors
// For license information, please see license.txt

frappe.ui.form.on("Training Attestation", {
	refresh(frm) {
        frm.trigger('fullname');
	},
    firstname(frm){
        frm.trigger('fullname');
    },
    lastname(frm){
        frm.trigger('fullname');
    },
    training(frm){
        frm.trigger('fullname');
    },
     async  fullname(frm){
        if(frm.doc.firstname && frm.doc.lastname && frm.doc.training) {
         let doc = await frappe.db.get_doc("Training",frm.doc.training)

        frm.set_value('title',`${frm.doc.firstname[0].toUpperCase()}${frm.doc.lastname[0].toUpperCase()}-${doc.title}`)
        }
    },
    before_save(frm){
        if(frm.doc.is_published) frm.set_value('route',`training-attestation/${frm.doc.name}`)
    }
});
