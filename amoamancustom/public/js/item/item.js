frappe.ui.form.on('Item',{
refresh(frm){
  if(frm.is_new){
    frm.toggle_reqd("item_name",1)
  }
},
item_group(frm){
    switch(frm.doc.item_group){
      case "Formation" :
          frm.set_value("naming_series","Formation-.YYYY.-");
          break;

      case "Gestion de projet interne":
          frm.set_value("naming_series","GPI-.YYYY.-");
          break;
      
      case "Assistance technique ou Mise a disposition (Positionnement de ressource)":
          frm.set_value("naming_series","MAD-.YYYY.-");
          break;
      
      case "Sourcing":
          frm.set_value("naming_series","Sourcing-.YYYY.-");
          break;
      case "Solution Pay-to-use":
          frm.set_value("naming_series","Solution-P2U-.YYYY.-");
          break;

      case "Gestion de Projet Externe (Gestion de ressource et du projet)":
          frm.set_value("naming_series","GPE-.YYYY.-");
          break;
      
      case "Mise en Conformité":
          frm.set_value("naming_series","MEC-.YYYY.-");
          break;
      
      default: 

         break;
  
    }
  }
});
