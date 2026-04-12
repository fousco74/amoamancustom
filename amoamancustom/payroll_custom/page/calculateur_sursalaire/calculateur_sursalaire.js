frappe.pages["calculateur-sursalaire"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Calculateur de Sursalaire"),
		single_column: true,
	});

	new SursalaireCalculateur(wrapper);
};

class SursalaireCalculateur {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;

		// État interne
		this._sursalaire_abbr = null;   // abréviation détectée depuis la structure
		this._extra_controls = {};       // contrôles dynamiques (clé = fieldname)
		this._extra_fieldtypes = {};     // types des contrôles dynamiques

		this.make_form();
	}

	// ─────────────────────────────────────────────────────────────
	// Construction du formulaire statique (7 champs principaux)
	// ─────────────────────────────────────────────────────────────
	make_form() {
		const $body = $(this.wrapper).find(".page-content");
		$body.empty();

		this.$container = $(`
			<div class="container-fluid" style="max-width:860px; padding-top:20px;">

				<!-- Carte 1 : Paramètres principaux -->
				<div class="card shadow-sm mb-3">
					<div class="card-header">
						<h6 class="mb-0 fw-semibold">${__("Paramètres principaux")}</h6>
					</div>
					<div class="card-body">
						<div class="row">
							<div class="col-md-6" id="field-grade"></div>
							<div class="col-md-6" id="field-grade-cat"></div>
						</div>
						<div class="row">
							<div class="col-md-6" id="field-base"></div>
							<div class="col-md-6" id="field-parts"></div>
						</div>
						<div class="row">
							<div class="col-md-6" id="field-structure"></div>
							<div class="col-md-6" id="field-net"></div>
						</div>
					</div>
				</div>

				<!-- Bandeau d'information sur la composante détectée -->
				<div id="detect-info" style="display:none;" class="mb-3">
					<div class="alert alert-info py-2 mb-0 d-flex align-items-center gap-3">
						<span id="info-structure"></span>
						<span id="info-composante"></span>
					</div>
				</div>

				<!-- Carte 2 : Variables complémentaires (dynamique) -->
				<div id="extra-card" class="card shadow-sm mb-4" style="display:none;">
					<div class="card-header">
						<h6 class="mb-0 fw-semibold">
							${__("Informations complémentaires")}
							<small class="text-muted fw-normal ms-2">${__("requises par cette structure salariale")}</small>
						</h6>
					</div>
					<div class="card-body" id="extra-fields-body">
						<!-- Groupes de champs rendus dynamiquement -->
					</div>
				</div>

				<!-- Bouton -->
				<div class="text-center mb-4">
					<button class="btn btn-primary btn-lg px-5" id="btn-calculer" disabled>
						${__("Calculer le Sur-salaire")}
					</button>
					<div id="calc-spinner" class="mt-2" style="display:none;">
						<div class="progress" style="height:4px;">
							<div class="progress-bar progress-bar-striped progress-bar-animated w-100"></div>
						</div>
					</div>
				</div>

				<!-- Carte 3 : Résultats -->
				<div id="calc-result" style="display:none;"></div>

			</div>
		`).appendTo($body);

		// ── Grade ──────────────────────────────────────────────
		this.$grade = this._make_link({
			fieldname: "grade",
			label: __("Grade"),
			options: "Employee Grade",
			reqd: 1,
			parent: "#field-grade",
		});
		this._on_link_select(this.$grade, () => this._on_grade_change());

		// ── Catégorie de Grade ──────────────────────────────────
		this.$grade_cat = this._make_link({
			fieldname: "grade_categorie",
			label: __("Catégorie de Grade"),
			options: "Grade Categorie",
			reqd: 1,
			parent: "#field-grade-cat",
		});
		this.$grade_cat.get_query = () => ({
			filters: { grade: this.$grade.get_value() || "__invalid__" },
		});
		this._on_link_select(this.$grade_cat, () => this._on_grade_cat_change());

		// ── Salaire de Base ────────────────────────────────────
		this.$base = this._make_ctrl({
			fieldtype: "Currency",
			fieldname: "base",
			label: __("Salaire de Base"),
			reqd: 1,
			description: __("Chargé automatiquement depuis la catégorie, modifiable"),
			parent: "#field-base",
		});

		// ── Nombre de Parts Fiscales ───────────────────────────
		this.$parts = this._make_ctrl({
			fieldtype: "Float",
			fieldname: "nombre_de_parts",
			label: __("Nombre de Parts Fiscales"),
			description: __("Ex. 1, 1.5, 2 — utilisé dans les formules ITS"),
			parent: "#field-parts",
		});
		this.$parts.set_value(1);

		// ── Structure Salariale ────────────────────────────────
		this.$structure = this._make_link({
			fieldname: "salary_structure",
			label: __("Structure Salariale"),
			options: "Salary Structure",
			reqd: 1,
			parent: "#field-structure",
		});
		this._on_link_select(this.$structure, () => this._on_structure_change());

		// ── Salaire Net Cible ──────────────────────────────────
		this.$net = this._make_ctrl({
			fieldtype: "Currency",
			fieldname: "net_cible",
			label: __("Salaire Net Cible"),
			reqd: 1,
			description: __("Le net que le salarié doit percevoir"),
			parent: "#field-net",
		});

		// ── Bouton calcul ──────────────────────────────────────
		this.$container.find("#btn-calculer").on("click", () => this._calculer());
	}

	// ─────────────────────────────────────────────────────────────
	// Helpers — création de contrôles Frappe
	// ─────────────────────────────────────────────────────────────

	_make_ctrl({ parent, ...df }) {
		const ctrl = frappe.ui.form.make_control({
			df,
			parent: this.$container.find(parent),
			render_input: true,
		});
		ctrl.refresh();
		return ctrl;
	}

	_make_link({ parent, fieldname, label, options, reqd, description }) {
		const ctrl = frappe.ui.form.make_control({
			df: { fieldtype: "Link", fieldname, label, options, reqd, description },
			parent: this.$container.find(parent),
			render_input: true,
		});
		ctrl.refresh();
		return ctrl;
	}

	// Écoute la sélection d'un champ Link (dropdown ou changement direct)
	_on_link_select(ctrl, handler) {
		$(ctrl.input_area).on("awesomplete-selectcomplete", () => setTimeout(handler, 50));
		$(ctrl.input_area).find("input").on("change", () => setTimeout(handler, 50));
	}

	// ─────────────────────────────────────────────────────────────
	// Handlers des champs principaux
	// ─────────────────────────────────────────────────────────────

	_on_grade_change() {
		this.$grade_cat.set_value("");
		this.$base.set_value("");
		this._reset_result();
	}

	_on_grade_cat_change() {
		const cat = this.$grade_cat.get_value();
		this._reset_result();
		if (!cat) return this.$base.set_value("");

		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Grade Categorie",
				fieldname: "salaire_de_base",
				filters: { name: cat },
			},
			callback: (r) => {
				if (r.message?.salaire_de_base != null) {
					this.$base.set_value(Math.round(r.message.salaire_de_base));
				}
			},
		});
	}

	_on_structure_change() {
		const structure = this.$structure.get_value();
		this._sursalaire_abbr = null;
		this._reset_detect_info();
		this._reset_extra_fields();
		this._reset_result();
		this.$container.find("#btn-calculer").prop("disabled", true);

		if (!structure) return;

		// Étape 1 : détecter la composante sursalaire
		frappe.call({
			method: "amoamancustom.payroll_custom.api.salary_calculator.get_salary_components",
			args: { salary_structure: structure },
			callback: (r) => {
				if (!r.message) return;

				const auto = r.message.earnings.find(
					(c) =>
						c.salary_component.toLowerCase().includes("sursalaire") ||
						c.abbr.toLowerCase().includes("sursal") ||
						c.abbr.toUpperCase() === "SS"
				);

				if (!auto) {
					frappe.msgprint({
						title: __("Composante introuvable"),
						message:
							__("Aucune composante de type « Sursalaire » trouvée dans la structure : ") +
							`<strong>${structure}</strong>.<br>` +
							__("Vérifiez que le nom de la composante contient « sursalaire » ou que son abréviation est « SS »."),
						indicator: "orange",
					});
					return;
				}

				this._sursalaire_abbr = auto.abbr;
				this._show_detect_info(structure, auto);

				// Étape 2 : détecter les variables complémentaires requises
				frappe.call({
					method: "amoamancustom.payroll_custom.api.salary_calculator.get_required_variables",
					args: { salary_structure: structure },
					callback: (r2) => {
						this._render_extra_fields(r2.message || []);
						this.$container.find("#btn-calculer").prop("disabled", false);
					},
				});
			},
		});
	}

	// ─────────────────────────────────────────────────────────────
	// Affichage de la banderole "structure + composante détectée"
	// ─────────────────────────────────────────────────────────────

	_show_detect_info(structure, composante) {
		this.$container.find("#info-structure").html(
			`<strong>${__("Structure")}&nbsp;:</strong> ${structure}`
		);
		this.$container.find("#info-composante").html(
			`<strong>${__("Composante sursalaire")}&nbsp;:</strong> ${composante.salary_component} <code>(${composante.abbr})</code>`
		);
		this.$container.find("#detect-info").show();
	}

	_reset_detect_info() {
		this.$container.find("#detect-info").hide();
		this.$container.find("#info-structure, #info-composante").html("");
	}

	// ─────────────────────────────────────────────────────────────
	// Rendu dynamique des champs complémentaires
	// ─────────────────────────────────────────────────────────────

	_render_extra_fields(groups) {
		this._extra_controls = {};
		this._extra_fieldtypes = {};

		const $body = this.$container.find("#extra-fields-body").empty();

		if (!groups || groups.length === 0) {
			this.$container.find("#extra-card").hide();
			return;
		}

		groups.forEach((group, gi) => {
			// Titre du groupe
			if (gi > 0) $body.append(`<hr class="my-3">`);
			$body.append(`
				<p class="fw-semibold mb-1 text-muted small text-uppercase">${group.label}</p>
				${group.description ? `<p class="text-muted small mb-2">${group.description}</p>` : ""}
			`);

			const $row = $(`<div class="row"></div>`).appendTo($body);
			const col_class = group.fields.length === 1 ? "col-md-6" : "col-md-6";

			group.fields.forEach((fd) => {
				const $col = $(`<div class="${col_class}" id="extra-${fd.fieldname}"></div>`).appendTo($row);

				const df = {
					fieldtype: fd.fieldtype,
					fieldname: fd.fieldname,
					label: fd.label,
					description: fd.description || "",
				};

				const ctrl = frappe.ui.form.make_control({
					df,
					parent: $col,
					render_input: true,
				});
				ctrl.refresh();

				// Valeur par défaut
				if (fd.default !== undefined && fd.default !== null) {
					ctrl.set_value(fd.default);
				} else if (fd.fieldtype === "Date") {
					ctrl.set_value(frappe.datetime.get_today());
				}

				this._extra_controls[fd.fieldname] = ctrl;
				this._extra_fieldtypes[fd.fieldname] = fd.fieldtype;
			});
		});

		this.$container.find("#extra-card").show();
	}

	_reset_extra_fields() {
		this._extra_controls = {};
		this._extra_fieldtypes = {};
		this.$container.find("#extra-fields-body").empty();
		this.$container.find("#extra-card").hide();
	}

	// ─────────────────────────────────────────────────────────────
	// Parsing robuste des nombres
	// Gère les deux formats : européen (129.313 = 129 313) et US (129,313)
	// ─────────────────────────────────────────────────────────────

	_robust_parse(raw) {
		if (raw === null || raw === undefined || raw === "") return 0;
		if (typeof raw === "number") return raw;

		// Supprimer les espaces et les caractères non numériques (sauf ., , -)
		let s = String(raw).trim().replace(/[^\d.,\-]/g, "");
		if (!s || s === "-") return 0;

		const has_comma  = s.includes(",");
		const has_period = s.includes(".");

		// Pas de séparateur : entier pur
		if (!has_comma && !has_period) return parseInt(s, 10) || 0;

		// Les deux séparateurs présents → le dernier est décimal
		if (has_comma && has_period) {
			const last_comma  = s.lastIndexOf(",");
			const last_period = s.lastIndexOf(".");
			if (last_period > last_comma) {
				// Format US : "1,234.56" → supprimer les virgules
				return parseFloat(s.replace(/,/g, "")) || 0;
			} else {
				// Format européen : "1.234,56" → supprimer les points, virgule → point
				return parseFloat(s.replace(/\./g, "").replace(",", ".")) || 0;
			}
		}

		// Seulement un point
		if (has_period) {
			const parts = s.split(".");
			// Heuristique : si toutes les parties après le 1er point ont exactement 3 chiffres
			// → c'est un séparateur de milliers (ex. "129.313", "1.234.567")
			const all_three = parts.slice(1).every(p => p.length === 3);
			if (all_three && parts.length >= 2) {
				return parseInt(s.replace(/\./g, ""), 10) || 0;
			}
			// Sinon : décimale (ex. "129.50")
			return parseFloat(s) || 0;
		}

		// Seulement une virgule
		if (has_comma) {
			const parts = s.split(",");
			const all_three = parts.slice(1).every(p => p.length === 3);
			if (all_three && parts.length >= 2) {
				// Séparateur de milliers US : "129,313"
				return parseInt(s.replace(/,/g, ""), 10) || 0;
			}
			// Décimale européenne : "129,50"
			return parseFloat(s.replace(",", ".")) || 0;
		}

		return 0;
	}

	// ─────────────────────────────────────────────────────────────
	// Lecture des valeurs des contrôles
	// ─────────────────────────────────────────────────────────────

	_get_value(ctrl, fieldtype) {
		if (fieldtype === "Date") return ctrl.get_value() || null;

		// Float / Int : Frappe gère lui-même le parsing → get_value() retourne
		// déjà la valeur numérique correcte (ex. "2.000" affiché → 2 retourné).
		// _robust_parse sur "2.000" donnerait 2000 (séparateur de milliers) — incorrect.
		if (fieldtype === "Float" || fieldtype === "Int") {
			return parseFloat(ctrl.get_value()) || 0;
		}

		// Currency et autres : lire le texte brut pour gérer le format européen
		// (ex. "129.313" = 129 313 FCFA avec point comme séparateur de milliers).
		const raw = ctrl.$input ? ctrl.$input.val() : ctrl.get_value();
		return this._robust_parse(raw);
	}

	_num(ctrl) {
		return this._get_value(ctrl, "Currency");
	}

	// ─────────────────────────────────────────────────────────────
	// Réinitialisation du résultat
	// ─────────────────────────────────────────────────────────────

	_reset_result() {
		this.$container.find("#calc-result").hide().empty();
	}

	// ─────────────────────────────────────────────────────────────
	// Calcul principal
	// ─────────────────────────────────────────────────────────────

	_calculer() {
		// Valeurs des champs principaux
		const grade = this.$grade.get_value();
		const grade_cat = this.$grade_cat.get_value();
		const base = this._num(this.$base);
		const nombre_de_parts = this._get_value(this.$parts, "Float") || 1;
		const salary_structure = this.$structure.get_value();
		const net_cible = this._num(this.$net);

		// Validation
		const errors = [];
		if (!grade) errors.push(__("Grade"));
		if (!grade_cat) errors.push(__("Catégorie de Grade"));
		if (!base) errors.push(__("Salaire de Base"));
		if (!salary_structure) errors.push(__("Structure Salariale"));
		if (!this._sursalaire_abbr) errors.push(__("Composante Sursalaire (non détectée)"));
		if (!net_cible) errors.push(__("Salaire Net Cible"));

		if (errors.length) {
			frappe.msgprint({
				title: __("Champs manquants"),
				message: __("Veuillez remplir : ") + errors.join(", "),
				indicator: "orange",
			});
			return;
		}

		// Collecte des variables complémentaires
		const extra = {};
		for (const [fieldname, ctrl] of Object.entries(this._extra_controls)) {
			extra[fieldname] = this._get_value(ctrl, this._extra_fieldtypes[fieldname]);
		}

		// Affichage du spinner
		this.$container.find("#btn-calculer").prop("disabled", true);
		this.$container.find("#calc-spinner").show();
		this._reset_result();

		frappe.call({
			method: "amoamancustom.payroll_custom.api.salary_calculator.calculer_sursalaire",
			args: {
				salary_structure,
				sursalaire_abbr: this._sursalaire_abbr,
				base,
				nombre_de_parts,
				net_cible,
				// Grade et catégorie — nécessaires pour les conditions sur les composantes
				grade,
				grade_cat,
				// Variables complémentaires détectées depuis la structure
				mois_paie: extra.mois_paie || null,
				anciennete_annees: extra.anciennete_annees || 0,
				anciennete_mois_supp: extra.anciennete_mois_supp || 0,
				conges_valides: extra.conges_valides || 0,
				payment_days: extra.payment_days || 26,
				total_working_days: extra.total_working_days || 26,
				avance_salaire: extra.avance_salaire || 0,
				prime_transport: extra.prime_transport || 0,
			},
			callback: (r) => {
				this.$container.find("#btn-calculer").prop("disabled", false);
				this.$container.find("#calc-spinner").hide();

				if (r.message?.success) {
					this._afficher_resultat(r.message);
				} else {
					const msg = r.message?.error || __("Erreur inattendue.");
					// Si debug présent (net sans sursalaire > net cible), afficher le détail
					if (r.message?.debug) {
						this._afficher_debug(r.message.debug, r.message.error);
					} else {
						frappe.msgprint({
							title: __("Impossible de calculer le sur-salaire"),
							message: msg,
							indicator: "orange",
						});
					}
				}
			},
			error: () => {
				this.$container.find("#btn-calculer").prop("disabled", false);
				this.$container.find("#calc-spinner").hide();
			},
		});
	}

	// ─────────────────────────────────────────────────────────────
	// Affichage d'un diagnostic quand net(0) > net_cible
	// ─────────────────────────────────────────────────────────────

	_afficher_debug(debug, error_msg) {
		const fmt = (v) =>
			frappe.format(flt(v), { fieldtype: "Currency" }, { only_value: false });

		const rows = (debug.detail_gains || []).map(
			(c) => `<tr><td>${c.label}</td><td class="text-end">${fmt(c.amount)}</td></tr>`
		).join("");

		this.$container.find("#calc-result").html(`
			<div class="alert alert-warning mb-3">
				<strong>${__("Sur-salaire impossible à calculer")}</strong><br>
				<small>${error_msg}</small>
			</div>
			<p class="text-muted small">${__("Détail du calcul sans sur-salaire (pour diagnostic) :")}</p>
			<div class="row">
				<div class="col-md-6">
					<table class="table table-sm table-bordered">
						<thead class="table-light">
							<tr><th>${__("Gains")}</th><th class="text-end">${__("Montant")}</th></tr>
						</thead>
						<tbody>${rows}</tbody>
						<tfoot>
							<tr class="fw-bold table-primary">
								<td>${__("Brut")}</td>
								<td class="text-end">${fmt(debug.brut)}</td>
							</tr>
						</tfoot>
					</table>
				</div>
				<div class="col-md-6">
					<div class="card border-warning">
						<div class="card-body text-center">
							<p class="text-muted mb-1 small">${__("Net obtenu sans sur-salaire")}</p>
							<h4 class="text-warning fw-bold">${fmt(debug.net_sans_sursalaire)}</h4>
							<p class="text-muted small mt-2">${__("Vérifiez que le salaire de base et le salaire net cible sont corrects.")}</p>
						</div>
					</div>
				</div>
			</div>
		`).show();
	}

	// ─────────────────────────────────────────────────────────────
	// Affichage du résultat
	// ─────────────────────────────────────────────────────────────

	_afficher_resultat(data) {
		const fmt = (v) =>
			frappe.format(flt(v), { fieldtype: "Currency" }, { only_value: false });

		const rows_gains = (data.detail_gains || [])
			.map(
				(c) => `
				<tr ${c.is_sursalaire ? 'class="table-warning fw-bold"' : (c.hors_brut ? 'class="text-muted"' : "")}>
					<td>
						${c.label}
						${c.is_sursalaire ? '<span class="badge bg-warning text-dark ms-1">calculé</span>' : ""}
						${c.hors_brut ? '<small class="text-muted ms-1">(hors brut)</small>' : ""}
					</td>
					<td class="text-end">${fmt(c.amount)}</td>
				</tr>`
			)
			.join("");

		const rows_retenues = (data.detail_retenues || [])
			.map(
				(c) => `
				<tr ${c.note ? 'class="text-muted"' : ""}>
					<td>${c.label}${c.note ? ` <small class="text-muted">(${c.note})</small>` : ""}</td>
					<td class="text-end">${fmt(c.amount)}</td>
				</tr>`
			)
			.join("");

		const ecart = flt(data.net_calcule) - flt(data.net_cible);
		const ecart_ok = Math.abs(ecart) <= 1;

		const ctx = data.contexte || {};
		const ctx_html = [
			ctx.start_date ? `${__("Période")} : <strong>${ctx.start_date.slice(0, 7)}</strong>` : "",
			ctx.anciennete_annees != null && ctx.anciennete_annees > 0
				? `${__("Ancienneté")} : <strong>${ctx.anciennete_annees} ans</strong>`
				: "",
			ctx.payment_days != null && ctx.payment_days !== ctx.total_working_days
				? `${__("Jours payés")} : <strong>${ctx.payment_days}/${ctx.total_working_days}</strong>`
				: "",
		]
			.filter(Boolean)
			.join(" &nbsp;|&nbsp; ");

		this.$container.find("#calc-result").html(`

			<!-- Résultat principal -->
			<div class="alert alert-success text-center mb-4 shadow-sm">
				<p class="mb-1 text-muted small">${__("Sur-salaire à appliquer")}</p>
				<h2 class="mb-0 fw-bold display-6">${fmt(data.sursalaire)}</h2>
			</div>

			<!-- Tableau détaillé -->
			<div class="row">
				<div class="col-md-6 mb-3">
					<table class="table table-sm table-bordered mb-0">
						<thead class="table-light">
							<tr><th colspan="2" class="text-center">${__("Gains")}</th></tr>
							<tr>
								<th>${__("Composante")}</th>
								<th class="text-end">${__("Montant")}</th>
							</tr>
						</thead>
						<tbody>${rows_gains || '<tr><td colspan="2" class="text-muted text-center">—</td></tr>'}</tbody>
						<tfoot>
							<tr class="table-primary fw-bold">
								<td>${__("Salaire Brut")}</td>
								<td class="text-end">${fmt(data.brut)}</td>
							</tr>
						</tfoot>
					</table>
				</div>

				<div class="col-md-6 mb-3">
					<table class="table table-sm table-bordered mb-0">
						<thead class="table-light">
							<tr><th colspan="2" class="text-center">${__("Retenues")}</th></tr>
							<tr>
								<th>${__("Composante")}</th>
								<th class="text-end">${__("Montant")}</th>
							</tr>
						</thead>
						<tbody>${rows_retenues || '<tr><td colspan="2" class="text-muted text-center">—</td></tr>'}</tbody>
						<tfoot>
							<tr class="table-danger fw-bold">
								<td>${__("Total Retenues")}</td>
								<td class="text-end">${fmt(data.total_retenues)}</td>
							</tr>
						</tfoot>
					</table>
				</div>
			</div>

			<!-- Récapitulatif net -->
			<div class="row g-2 mb-3">
				<div class="col-md-4">
					<div class="card text-center border-primary">
						<div class="card-body py-2">
							<small class="text-muted">${__("Salaire Brut")}</small>
							<div class="fw-bold">${fmt(data.brut)}</div>
						</div>
					</div>
				</div>
				<div class="col-md-4">
					<div class="card text-center border-danger">
						<div class="card-body py-2">
							<small class="text-muted">${__("Total Retenues")}</small>
							<div class="fw-bold text-danger">${fmt(data.total_retenues)}</div>
						</div>
					</div>
				</div>
				<div class="col-md-4">
					<div class="card text-center ${ecart_ok ? "border-success" : "border-warning"}">
						<div class="card-body py-2">
							<small class="text-muted">${__("Salaire Net Obtenu")}</small>
							<div class="fw-bold ${ecart_ok ? "text-success" : "text-warning"}">${fmt(data.net_calcule)}</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Écart et contexte -->
			<div class="alert ${ecart_ok ? "alert-success" : "alert-warning"} py-2 mb-2 text-center">
				${ecart_ok
					? `<strong>${__("Net cible atteint")} ✓</strong> — écart : ${fmt(ecart)}`
					: `<strong>${__("Écart résiduel")} : ${fmt(ecart)}</strong>
					   <small class="d-block text-muted">${__("Un léger écart peut provenir des arrondis fiscaux.")}</small>`
				}
			</div>
			${ctx_html ? `<p class="text-muted small text-center mb-0">${ctx_html}</p>` : ""}

		`).show();

		// Scroll vers le résultat
		setTimeout(() => {
			this.$container.find("#calc-result")[0].scrollIntoView({ behavior: "smooth", block: "start" });
		}, 100);
	}
}
