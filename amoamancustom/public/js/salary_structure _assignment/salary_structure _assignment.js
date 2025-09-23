frappe.ui.form.on('Salary Structure Assignment', {
	employee(frm){


    if(frm.doc.employee){
        frappe.db.get_value("Employee",frm.doc.employee, "custom_catégorie_").then((r => {
        
            if(r.message && r.message.custom_catégorie_){
                console.log("data :", r.message.custom_catégorie_)
                frappe.db.get_value('Grade Categorie', r.message.custom_catégorie_, 'salaire_de_base').then(val =>{
                    console.log(val)
                    if(val.message && val.message.salaire_de_base){
                        frm.set_value("base",val.message.salaire_de_base)
                    }
                })
            }
        }))
    }

    }
})