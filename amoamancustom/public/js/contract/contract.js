frappe.ui.form.on('Contract',{
refresh(frm){
    const userRoles = frappe.boot.user.roles;

        // Définir les options du champ selon les rôles
        if (userRoles.includes("Sales Manager")) {
            frm.set_df_property('party_type', 'options', ['Customer', 'Supplier']);

        } 
        else if(userRoles.includes("HR Manager") || userRoles.includes("System Manager") ) {
            frm.set_df_property('party_type', 'options', ['Employee']);
        } 

}
});
