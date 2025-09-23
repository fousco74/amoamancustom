frappe.ui.form.on('Employee', {
  refresh(frm) {
    frm.trigger('part_number');
  },
   custom_length_of_service_year(frm){
    const value = frm.doc.custom_length_of_service_year>=2  ? true : false;

    frm.set_value("custom_has_seniority_bonus", value);
    },

  // Recalcule les parts dès qu'un champ pertinent change
  custom_statut_matrimonial_et_charge_de_famille(frm) { frm.trigger('part_number'); },
  custom_nombre_total_denfant(frm)                   { frm.trigger('part_number'); },
  custom_nombre_denfant_infirme(frm)                { frm.trigger('part_number'); },

  // --- Calcul du nombre de parts (N) ---
  part_number(frm) {
    const statusRaw = (frm.doc.custom_statut_matrimonial_et_charge_de_famille || '').toLowerCase();
    const nbEnfants  = parseInt(frm.doc.custom_nombre_total_denfant, 10) || 0;
    const nbInfirme  = parseInt(frm.doc.custom_nombre_denfant_infirme, 10) || 0;

    // Normalisation du statut
    const isCelibDiv = statusRaw.includes('célib') || statusRaw.includes('celib') || statusRaw.includes('divorc');
    const isMarie    = statusRaw.includes('mari');
    const isVeuf     = statusRaw.includes('veuf');

    let parts = 1; // valeur par défaut (célib/veuf sans enfant)

    if (isCelibDiv) {
      if (nbEnfants === 0) {
        parts = 1;
      } else {
        // Célibataire/Divorcé avec enfants : 2 + 0,5 par enfant au-delà du 1er
        parts = 2 + (nbEnfants - 1) * 0.5;
        console.log("parts ",parts)

      }
    } else if (isMarie) {
      if (nbEnfants === 0) {
        parts = 2;
      } else {

        console.log(parts)
        // Marié avec enfants : 2,5 + 0,5 par enfant au-delà du 1er
        parts = 2.5 + (nbEnfants - 1) * 0.5;

      }
    } else if (isVeuf) {
      if (nbEnfants === 0) {
        parts = 1; // veuf sans enfant
      } else {
        // Veuf avec enfants : même barème que marié
        parts = 2.5 + (nbEnfants - 1) * 0.5;
      }
    }

    // +1 part par enfant infirme (même majeur)
    parts += nbInfirme * 0.5;

    // Plafond à 5 parts (cohérent avec le barème RICF fourni)
    parts = Math.min(5, parts);

    frm.set_value('custom_nbre_de_parts', parts);
  },

});
