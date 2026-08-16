"""Bulletin de paie ivoirien : brute imposable, solde de tout compte, bareme ITS.

Porte depuis paie_ci/paie_ci/overrides/salary_slip.py, adapte a HRMS 16.16.

Quatre drapeaux poses sur la Salary Component pilotent le calcul :

    custom_variable_based_on_taxe_applicable_component
        montant = somme des gains « Is Tax Applicable » du bulletin courant.
    custom_gross_pay_over__the_last_12_or_less
        montant = moyenne mensuelle du brut imposable sur les 12 derniers
        bulletins soumis (ou moins), bornee par la date d'embauche.
    custom_sum_gross_pay_on_contract
        montant = cumul du brut imposable sur la periode du CDD.
    custom_print_on_salary_slip
        purement d'affichage, consomme par le format d'impression.

Pourquoi injecter dans le contexte d'evaluation plutot que d'ecrire row.amount
apres coup : depuis HRMS 16.16 les formules sont evaluees en UNE passe par table
(add_structure_components, salary_slip.py:1195), tous les abbr etant
pre-initialises a 0 par get_component_abbr_map(). Une valeur posee apres
super().calculate_component_amounts("earnings") serait donc invisible aux
formules des autres gains de la meme passe — or moy_brut_imp alimente
l'indemnite de conge, de preavis, de licenciement et de retraite, qui sont
toutes des gains. On surcharge donc get_data_for_eval(), appele au debut de
chaque passe, pour semer les valeurs avant toute evaluation.
"""

import frappe
from frappe import _
from frappe.utils import add_months, cint, flt, getdate
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

# Drapeaux Salary Component, par ordre de priorite si plusieurs sont coches.
FLAG_TAXABLE_SUM = "custom_variable_based_on_taxe_applicable_component"
FLAG_AVG_12M = "custom_gross_pay_over__the_last_12_or_less"
FLAG_CONTRACT_SUM = "custom_sum_gross_pay_on_contract"
CUSTOM_SOURCE_FLAGS = (FLAG_TAXABLE_SUM, FLAG_AVG_12M, FLAG_CONTRACT_SUM)

# Quatrieme source : le drapeau standard variable_based_on_taxable_salary, dont
# on remplace le calcul HRMS (annualise) par le bareme ITS mensuel ivoirien.
FLAG_ITS_SLAB = "variable_based_on_taxable_salary"


class CustomSalarySlip(SalarySlip):
    # ------------------------------------------------------------------
    # Composantes pilotees par un champ custom
    # ------------------------------------------------------------------

    def _component_flag(self, salary_component):
        """Retourne le drapeau custom actif sur cette Salary Component, ou None."""
        if not salary_component:
            return None
        cache = self.__dict__.setdefault("_component_flag_cache", {})
        if salary_component in cache:
            return cache[salary_component]

        flag = None
        try:
            values = frappe.get_cached_value(
                "Salary Component", salary_component, CUSTOM_SOURCE_FLAGS, as_dict=True
            )
            for name in CUSTOM_SOURCE_FLAGS:
                if values and cint(values.get(name)):
                    flag = name
                    break
        except Exception:
            # Champs absents (migration pas encore passee) : on ne bloque pas la paie.
            frappe.log_error(frappe.get_traceback(), "CUSTOM_SOURCE_FLAG_ERROR")

        cache[salary_component] = flag
        return flag

    def _custom_source_rows(self):
        """Lignes de structure (deja filtrees sur leur `condition` par la SSA)
        dont le montant vient de nous, sous la forme [(component_type, row, flag)].

        Le drapeau ITS est lu sur la LIGNE de structure (que HRMS renseigne
        depuis le master via set_missing_values), les trois autres sur le master.
        """
        evaluated = getattr(self, "_evaluated_components", None) or {}
        rows = []
        for component_type in ("earnings", "deductions"):
            for struct_row in evaluated.get(component_type) or []:
                if cint(struct_row.get(FLAG_ITS_SLAB)):
                    rows.append((component_type, struct_row, FLAG_ITS_SLAB))
                    continue
                flag = self._component_flag(struct_row.salary_component)
                if flag:
                    rows.append((component_type, struct_row, flag))
        return rows

    def _amount_for_flag(self, flag):
        """Montant a poser, ou None quand on n'a rien a dire (l'appelant laisse
        alors le comportement HRMS standard)."""
        if flag == FLAG_TAXABLE_SUM:
            return self._get_taxable_earnings_sum()
        if flag == FLAG_AVG_12M:
            return self._get_avg_12m_taxable()
        if flag == FLAG_CONTRACT_SUM:
            return self._get_contract_sum_amount()
        if flag == FLAG_ITS_SLAB:
            return self._calculate_its_ci(self._get_taxable_earnings_sum())
        return 0.0

    def _custom_source_amounts(self):
        """{abbr: montant} pour les composantes dont le montant vient de nous.

        Volontairement non memorise : la somme des gains imposables — et donc
        l'ITS qui en decoule — change entre la passe earnings et la passe
        deductions. Les deux sources couteuses (moyenne 12 mois, cumul CDD) ont
        leur propre cache.
        """
        amounts = {}
        for _component_type, struct_row, flag in self._custom_source_rows():
            amount = self._amount_for_flag(flag)
            if amount is not None:
                amounts[struct_row.abbr] = amount
        return amounts

    # ------------------------------------------------------------------
    # Sources de valeurs
    # ------------------------------------------------------------------

    def _get_taxable_earnings_sum(self):
        """Somme des gains du bulletin dont la ligne porte is_tax_applicable."""
        return flt(
            sum(
                flt(row.amount)
                for row in (self.earnings or [])
                if cint(getattr(row, "is_tax_applicable", 0))
            ),
            2,
        )

    def _flagged_component_names(self, flag):
        """Composantes portant `flag`, tous bulletins confondus (lecture DB).

        Sert a retrouver, dans l'historique des bulletins soumis, les lignes qui
        materialisent le brut imposable.
        """
        return frappe.get_all("Salary Component", filters={flag: 1}, pluck="name")

    def _sum_details_for_slips(self, slip_names):
        """Somme des Salary Detail « brute imposable » sur une liste de bulletins."""
        if not slip_names:
            return 0.0
        flagged = self._flagged_component_names(FLAG_TAXABLE_SUM)
        if not flagged:
            return 0.0
        rows = frappe.get_all(
            "Salary Detail",
            filters=[
                ["parent", "in", slip_names],
                ["parenttype", "=", "Salary Slip"],
                ["salary_component", "in", flagged],
            ],
            fields=["amount"],
        )
        return flt(sum(flt(r.amount) for r in rows), 2)

    def _get_avg_12m_taxable(self):
        """Moyenne mensuelle du brut imposable sur la fenetre des 12 mois
        precedant start_date (bulletin courant exclu), bornee par la date
        d'embauche. Aucun bulletin trouve -> 0. Resultat memorise.
        """
        cached = getattr(self, "_avg_12m_taxable_cache", None)
        if cached is not None:
            return cached

        avg_value = 0.0
        try:
            start_date_courant = getdate(self.start_date)
            window_start = add_months(start_date_courant, -12)

            doj = frappe.db.get_value("Employee", self.employee, "date_of_joining")
            if doj and getdate(doj) > getdate(window_start):
                window_start = getdate(doj)

            slip_names = frappe.get_all(
                "Salary Slip",
                filters=[
                    ["employee", "=", self.employee],
                    ["docstatus", "=", 1],
                    ["name", "!=", self.name],
                    ["start_date", ">=", window_start],
                    ["start_date", "<", start_date_courant],
                ],
                pluck="name",
                order_by="start_date desc",
                limit=12,
            )
            if slip_names:
                avg_value = flt(self._sum_details_for_slips(slip_names) / len(slip_names), 2)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "AVG_12M_CALC_ERROR")

        self._avg_12m_taxable_cache = avg_value
        return avg_value

    def _get_contract_dates(self):
        """(debut, fin) du CDD de l'employe, en bloquant si l'un manque.

        Le blocage n'est atteint que si une composante
        custom_sum_gross_pay_on_contract concerne reellement ce bulletin : les
        lignes dont la `condition` est fausse sont deja exclues de
        _evaluated_components par la Salary Structure Assignment, donc
        _custom_source_amounts ne demande pas la valeur.
        """
        debut, fin = frappe.db.get_value(
            "Employee", self.employee, ["custom_date_debut_cdd", "custom_date_fin_cdd"]
        )
        if not debut or not fin:
            frappe.throw(
                _(
                    "Dates de CDD manquantes pour l'employé {0}. Renseignez "
                    "« Date début CDD » et « Date fin CDD » sur la fiche employé "
                    "avant de calculer cette composante."
                ).format(self.employee)
            )
        return getdate(debut), getdate(fin)

    def _get_contract_taxable_sum(self):
        """Cumul du brut imposable sur les bulletins SOUMIS dont start_date tombe
        dans la periode du CDD. Bulletin courant exclu. Resultat memorise."""
        cached = getattr(self, "_contract_taxable_sum_cache", None)
        if cached is not None:
            return cached

        debut, fin = self._get_contract_dates()

        total = 0.0
        try:
            slip_names = frappe.get_all(
                "Salary Slip",
                filters=[
                    ["employee", "=", self.employee],
                    ["docstatus", "=", 1],
                    ["name", "!=", self.name],
                    ["start_date", ">=", debut],
                    ["start_date", "<=", fin],
                ],
                pluck="name",
            )
            total = self._sum_details_for_slips(slip_names)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "CONTRACT_SUM_CALC_ERROR")

        self._contract_taxable_sum_cache = total
        return total

    def _get_contract_sum_amount(self):
        """Cumul CDD des bulletins soumis + contribution du bulletin COURANT,
        cette derniere seulement si sa start_date tombe dans la periode du CDD."""
        total = self._get_contract_taxable_sum()
        debut, fin = self._get_contract_dates()
        if debut <= getdate(self.start_date) <= fin:
            total = flt(total + self._get_taxable_earnings_sum(), 2)
        return total

    # ------------------------------------------------------------------
    # Injection dans le contexte d'evaluation
    # ------------------------------------------------------------------

    def get_data_for_eval(self):
        data, default_data = super().get_data_for_eval()
        try:
            for abbr, value in self._custom_source_amounts().items():
                data[abbr] = value
                default_data[abbr] = value
        except frappe.ValidationError:
            # frappe.throw legitime (dates de CDD manquantes) : on laisse remonter.
            raise
        except Exception:
            frappe.log_error(frappe.get_traceback(), "CUSTOM_SOURCE_SEED_ERROR")
        return data, default_data

    def add_structure_component(self, struct_row, component_type):
        """Ne pas laisser HRMS reevaluer une composante statistique pilotee par un
        champ custom : sa valeur est deja dans self.data / self.default_data, et
        le traitement standard des lignes statistiques (salary_slip.py:1218) la
        remettrait a 0. Les composantes non statistiques gardent le traitement
        standard : leur ligne doit apparaitre sur le bulletin, elle est ensuite
        renseignee par _apply_custom_source_components.
        """
        if struct_row.statistical_component and self._component_flag(struct_row.salary_component):
            return
        super().add_structure_component(struct_row, component_type)

    def _apply_custom_source_components(self, component_type):
        """Renseigne le montant des lignes non statistiques pilotees par un champ
        custom, et reinsere celles que HRMS a supprimees (remove_if_zero_valued
        avec un montant nul a l'evaluation)."""
        rows = self.get(component_type) or []
        present = {row.salary_component: row for row in rows if row.salary_component}

        for row_component_type, struct_row, flag in self._custom_source_rows():
            if row_component_type != component_type or struct_row.statistical_component:
                continue
            amount = self._amount_for_flag(flag)
            if amount is None:
                # Aucun bareme ITS configure -> on laisse le calcul HRMS standard.
                continue
            row = present.get(struct_row.salary_component)
            if row:
                row.amount = amount
                continue
            try:
                self.update_component_row(
                    struct_row,
                    amount,
                    component_type,
                    data=self.data,
                    remove_if_zero_valued=False,
                )
            except Exception:
                frappe.log_error(frappe.get_traceback(), "CUSTOM_SOURCE_READD_ROW_ERROR")

    # ------------------------------------------------------------------
    # ITS Cote d'Ivoire : bareme applique au mensuel imposable
    # ------------------------------------------------------------------

    def _get_income_tax_slab_name(self):
        """Nom de l'Income Tax Slab associe a ce bulletin, ou None."""
        try:
            slab = self._get_ssa_doc().income_tax_slab
            if slab:
                return slab
        except Exception:
            pass

        rows = frappe.get_all(
            "Salary Structure Assignment",
            filters={
                "employee": self.employee,
                "from_date": ("<=", self.start_date),
                "docstatus": 1,
            },
            fields=["income_tax_slab"],
            order_by="from_date desc",
            limit=1,
        )
        return (rows[0].get("income_tax_slab") or None) if rows else None

    def _calculate_its_ci(self, taxable_monthly):
        """Applique le bareme ITS directement sur le salaire mensuel imposable,
        sans annualisation.

        Pour chaque tranche (triees par `from` croissant) :
          - non atteinte  (X <= from)               -> 0, arret
          - derniere tr.  (to = 0, X > from)        -> (X - from) * taux, arret
          - atterrissage  (from < X <= to)          -> (X - from) * taux, arret
          - traversee, `from` finit par 0           -> (to - from) * taux
          - traversee, `from` ne finit pas par 0    -> (to - (from - 1)) * taux

        Retourne None si aucun Income Tax Slab n'est configure : l'appelant
        conserve alors le calcul standard HRMS.
        """
        slab_name = self._get_income_tax_slab_name()
        if not slab_name:
            return None

        try:
            slab_doc = frappe.get_cached_doc("Income Tax Slab", slab_name)
        except Exception:
            return None

        standard_exemption = flt(getattr(slab_doc, "standard_tax_exemption_amount", 0))
        x = max(flt(taxable_monthly) - standard_exemption, 0.0)

        total_tax = 0.0
        for slab in sorted(slab_doc.slabs, key=lambda s: flt(s.from_amount)):
            from_amt = flt(slab.from_amount)
            to_amt = flt(slab.to_amount)
            rate = flt(slab.percent_deduction) / 100.0

            if x <= from_amt:
                break

            if to_amt == 0 or x <= to_amt:
                total_tax += (x - from_amt) * rate
                break

            from_int = int(from_amt)
            if from_int == 0 or (from_int % 10 == 0):
                total_tax += (to_amt - from_amt) * rate
            else:
                total_tax += (to_amt - (from_amt - 1)) * rate

        return flt(total_tax, 2)

    def get_tax_components(self) -> list:
        """Neutralise l'injection des composantes fiscales depuis le master.

        HRMS, quand une structure salariale ne declare aucune composante
        variable_based_on_taxable_salary, ajoute d'autorite au bulletin TOUTES
        celles du master (salary_slip.py:1607). Notre composante « Retenue ITS
        Brut (barème) » se retrouverait donc sur les bulletins de Base Officiel,
        qui calcule deja son ITS par formule — double imposition.

        Ici les composantes fiscales sont pilotees par la structure salariale, et
        seulement par elle.
        """
        return []

    def calculate_variable_based_on_taxable_salary(self, tax_component):
        """Evite le msgprint HRMS « Start and end dates not in a valid Payroll
        Period » sur chaque bulletin.

        Le bareme ITS ivoirien s'applique directement au mensuel imposable, sans
        annualisation : aucun Payroll Period n'est requis, et le montant est pose
        par _apply_custom_source_components. On ne court-circuite HRMS que si un
        Income Tax Slab est bien configure ; sinon le comportement standard (et
        son message) est conserve.
        """
        if not self.payroll_period and self._get_income_tax_slab_name():
            return
        return super().calculate_variable_based_on_taxable_salary(tax_component)

    # ------------------------------------------------------------------
    # Solde de conges payes, alimente cote serveur
    # ------------------------------------------------------------------

    def _set_leave_balance_field(self):
        """Renseigne custom_leave_balance avec le solde de conges payes a end_date.

        Indispensable cote serveur : public/js/salary_slip/salary_slip.js ne
        s'execute pas lors d'une generation via Payroll Entry, job ou API. Sans
        ca custom_leave_balance vaut 0 au moment de l'evaluation des formules, et
        l'« Indemnite de conge » (custom_leave_balance * moy_brut_imp / 30) vaut 0
        puis est supprimee par remove_if_zero_valued. Resultat memorise.

        La valeur est aussi recopiee sur l'EMPLOYE. Raison : la Salary Structure
        Assignment pre-evalue toutes les formules dans un contexte bati par
        get_component_eval_context (hrms/payroll/utils.py:89) = abbr des
        composantes + SALARY_SLIP_EVAL_DEFAULTS + champs de la SSA + champs de
        l'employe. Les champs custom du BULLETIN n'y figurent pas : une formule
        citant custom_leave_balance y leve « name 'custom_leave_balance' is not
        defined » avant meme que le bulletin ne calcule quoi que ce soit. Le
        miroir cote employe donne le nom a resoudre ; a la passe du bulletin,
        c'est la valeur du bulletin qui gagne (get_data_for_eval superpose
        self.as_dict() en dernier, salary_slip.py:1285).

        Meme convention que get_paid_leave_days pour
        custom_validated_paid_leave_days : ecriture directe sans toucher au
        `modified` de l'employe.
        """
        if not self.meta.has_field("custom_leave_balance"):
            return

        cached = getattr(self, "_leave_balance_cache", None)
        if cached is None:
            from amoamancustom.api import get_leave_balance

            cached = 0.0
            try:
                cached = flt(get_leave_balance(self.employee, date=self.end_date) or 0)
            except Exception:
                frappe.log_error(frappe.get_traceback(), "LEAVE_BALANCE_CALC_ERROR")
            self._leave_balance_cache = cached

            try:
                if frappe.get_meta("Employee").has_field("custom_leave_balance"):
                    frappe.db.set_value(
                        "Employee",
                        self.employee,
                        "custom_leave_balance",
                        cached,
                        update_modified=False,
                    )
                    # get_component_eval_context lit l'employe via get_cached_doc.
                    frappe.clear_document_cache("Employee", self.employee)
            except Exception:
                frappe.log_error(frappe.get_traceback(), "LEAVE_BALANCE_MIRROR_ERROR")

        self.custom_leave_balance = cached

    # ------------------------------------------------------------------
    # Point d'entree
    # ------------------------------------------------------------------

    def calculate_component_amounts(self, component_type):
        # Avant l'evaluation des formules HRMS : sinon custom_leave_balance = 0
        # cote serveur -> « Indemnite de conge » = 0 -> ligne supprimee.
        self._set_leave_balance_field()

        super().calculate_component_amounts(component_type)

        self._apply_custom_source_components(component_type)
