{# ----------------------- Template Email pour Nouveau Prospect ERPNext - AMOAMAN ----------------------- #}

{# ----------------------- Pré-calcul / mapping robuste des champs ----------------------- #}
{%- set first_name = (doc.get('first_name') or doc.get('prenom') or doc.get('Prénom') or '') -%}
{%- set last_name  = (doc.get('last_name') or doc.get('nom') or '') -%}
{%- set email_id   = (doc.get('email_id') or doc.get('email') or '') -%}
{%- set job_title  = (doc.get('job_title') or doc.get('fonction') or '') -%}
{%- set whatsapp   = (doc.get('whatsapp_no') or doc.get('whatsapp') or doc.get('phone') or '') -%}

{%- set company_name   = doc.get('company_name') or doc.get("nom_de_lentreprise") or doc.get('Nom_de_lentreprise') or '' -%}
{%- set secteur        = doc.get('custom_secteur_dactivité') or doc.get('custom_secteur_dactivite') or doc.get('custom_secteur') or '' -%}
{%- set activite_autres = doc.get('custom_activite_autres') or doc.get('custom_activite_autres_') or doc.get('custom_activite_autre') or '' -%}
{%- set no_of_employees = doc.get('no_of_employees') or doc.get('no_of_employes') or '' -%}

{%- set m_compta  = doc.get('custom_comptabilité_finance') or doc.get('custom_comptabilite_finance') or doc.get('custom_comptabilite_finance') or False -%}
{%- set m_immob   = doc.get('custom_immobilisation') or False -%}
{%- set m_achats  = doc.get('custom_achats') or False -%}
{%- set m_stocks  = doc.get('custom_gestion_des_stocks') or doc.get('custom_gestion_stocks') or False -%}
{%- set m_ventes  = doc.get('custom_ventes__crm') or doc.get('custom_ventes_crm') or False -%}
{%- set m_pos     = doc.get('custom_point_de_vente') or doc.get('custom_point_de_vente_') or False -%}
{%- set m_rh      = doc.get('custom_ressources_humaines__paie') or doc.get('custom_ressources_humaines_paie') or False -%}
{%- set m_prod    = doc.get('custom_gestion_de_la_production') or False -%}
{%- set m_qual    = doc.get('custom_qualité') or doc.get('custom_qualite') or False -%}
{%- set m_projet  = doc.get('custom_projet') or False -%}
{%- set m_support = doc.get('custom_assistance_support') or False -%}

{%- set mig_clients      = doc.get('custom_clients') or doc.get('custom_clients_') or False -%}
{%- set mig_fournisseurs = doc.get('custom_fournisseurs') or False -%}
{%- set mig_produits     = doc.get('custom_produits_etou_services') or doc.get('custom_produits_etou_services_') or False -%}
{%- set mig_factures     = doc.get('custom_factures') or False -%}
{%- set mig_stocks       = doc.get('custom_stocks') or False -%}
{%- set mig_salaries     = doc.get('custom_salariés') or doc.get('custom_salaries') or False -%}

{%- set logiciel       = doc.get('custom_logiciel') or doc.get('custom_logiciel_') or '' -%}
{%- set si_oui_laquelle = doc.get('custom_si_oui_laquele') or doc.get('custom_si_oui_laquelle') or '' -%}
{%- set have_cahier    = doc.get('custom_avezvous_un_cahier_de_charge') or doc.get('custom_avezvous_un_cahier_de_charge_') or '' -%}
{%- set stade          = doc.get('custom_a_quel_stade_êtesvous') or doc.get('custom_a_quel_stade_etesvous') or '' -%}

{%- set besoin = doc.get('custom_décrivez_brièvement_votre_besoin_ou_vos_attentes') or doc.get('custom_decrivez_brievement_votre_besoin_ou_vos_attentes') or '' -%}
{%- set autres = doc.get('custom_autres') or '' -%}

{%- set has_modules   = m_compta or m_immob or m_achats or m_stocks or m_ventes or m_pos or m_rh or m_prod or m_qual or m_projet or m_support -%}
{%- set has_migration = mig_clients or mig_fournisseurs or mig_produits or mig_factures or mig_stocks or mig_salaries -%}

<!DOCTYPE html>
<html lang="fr" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="x-apple-disable-message-reformatting">
<title>Nouveau Prospect ERPNext</title>
<!--[if mso]>
<noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
<![endif]-->
<style>
  body, table, td, p, a { -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }
  table, td { mso-table-lspace:0pt; mso-table-rspace:0pt; }
  img { -ms-interpolation-mode:bicubic; border:0; height:auto; line-height:100%; outline:none; text-decoration:none; }
  body { margin:0; padding:0; width:100% !important; background-color:#f0f4f8; }
  #outlook a { padding:0; }
  .ReadMsgBody, .ExternalClass { width:100%; }
  .ExternalClass, .ExternalClass p, .ExternalClass td,
  .ExternalClass div, .ExternalClass span, .ExternalClass font { line-height:100%; }
</style>
</head>
<body style="margin:0;padding:0;background-color:#f0f4f8;font-family:Segoe UI,Helvetica,Arial,sans-serif;">

<!--[if mso]><table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" align="center"><tr><td><![endif]-->
<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" width="100%" style="max-width:600px;background-color:#f0f4f8;">
<tr><td style="padding:24px 16px;">

  <!-- ═══ CARD wrapper ═══ -->
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#ffffff;border-radius:16px;overflow:hidden;">

    <!-- ══════════════════════════════════════
         HERO — Gradient rouge→bleu via VML
    ══════════════════════════════════════ -->
    <tr>
      <td style="padding:0;">

        <!--[if mso]>
        <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width:600px;">
          <v:fill type="gradient" color="#F32A57" color2="#0756C5" angle="135"/>
          <v:textbox inset="30px,45px,30px,45px" style="mso-fit-shape-to-text:true;">
        <![endif]-->

        <div style="background:linear-gradient(135deg,#F32A57 0%,#0756C5 100%);padding:45px 30px;text-align:center;">
          <h1 style="margin:0 0 8px;font-size:28px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#ffffff;letter-spacing:-0.5px;mso-line-height-rule:exactly;">
            Nouveau Prospect
          </h1>
          <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#ffffff;mso-line-height-rule:exactly;">
            Demande de soumission ERPNext reçue
          </p>
        </div>

        <!--[if mso]>
          </v:textbox>
        </v:rect>
        <![endif]-->

      </td>
    </tr>

    <!-- ══════════════════════════════════════
         CONTENT
    ══════════════════════════════════════ -->
    <tr>
      <td style="padding:36px 30px 10px;">


        <!-- ─── SECTION : Contact Principal ─── -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:32px;">

          <!-- Section header -->
          <tr>
            <td style="padding-bottom:14px;border-bottom:2px solid #F32A57;">
              <p style="margin:0;font-size:15px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#032A5F;text-transform:uppercase;letter-spacing:0.8px;">
                &#128100;&nbsp; Contact Principal
              </p>
            </td>
          </tr>
          <tr><td style="padding-bottom:16px;font-size:1px;line-height:1px;">&nbsp;</td></tr>

          <!-- Prénom + Nom -->
          <tr>
            <td style="padding-bottom:14px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td width="49%" style="vertical-align:top;padding-right:8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Prénom</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ first_name or '—' }}</p>
                      </td></tr>
                    </table>
                  </td>
                  <td width="2%">&nbsp;</td>
                  <td width="49%" style="vertical-align:top;padding-left:8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Nom</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ last_name or '—' }}</p>
                      </td></tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Fonction + Email -->
          <tr>
            <td style="padding-bottom:14px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td width="49%" style="vertical-align:top;padding-right:8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Fonction</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ job_title or '—' }}</p>
                      </td></tr>
                    </table>
                  </td>
                  <td width="2%">&nbsp;</td>
                  <td width="49%" style="vertical-align:top;padding-left:8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Email</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        {% if email_id %}
                        <a href="mailto:{{ email_id }}" style="font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-decoration:none;word-break:break-all;">{{ email_id }}</a>
                        {% else %}
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#95a5a6;font-style:italic;">—</p>
                        {% endif %}
                      </td></tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- WhatsApp (pleine largeur) -->
          <tr>
            <td style="padding-bottom:8px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                <tr><td style="padding:16px 16px 4px;">
                  <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">WhatsApp</p>
                </td></tr>
                <tr><td style="padding:4px 16px 16px;">
                  <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ whatsapp or '—' }}</p>
                </td></tr>
              </table>
            </td>
          </tr>

        </table>


        <!-- ─── SECTION : Entreprise ─── -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:32px;">

          <tr>
            <td style="padding-bottom:14px;border-bottom:2px solid #F32A57;">
              <p style="margin:0;font-size:15px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#032A5F;text-transform:uppercase;letter-spacing:0.8px;">
                &#127962;&nbsp; Entreprise
              </p>
            </td>
          </tr>
          <tr><td style="padding-bottom:16px;font-size:1px;line-height:1px;">&nbsp;</td></tr>

          <!-- Nom entreprise (pleine largeur) -->
          <tr>
            <td style="padding-bottom:14px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                <tr><td style="padding:16px 16px 4px;">
                  <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Nom</p>
                </td></tr>
                <tr><td style="padding:4px 16px 16px;">
                  <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ company_name or '—' }}</p>
                </td></tr>
              </table>
            </td>
          </tr>

          <!-- Secteur + Taille -->
          <tr>
            <td style="padding-bottom:14px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td width="49%" style="vertical-align:top;padding-right:8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Secteur</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ secteur or '—' }}</p>
                      </td></tr>
                    </table>
                  </td>
                  <td width="2%">&nbsp;</td>
                  <td width="49%" style="vertical-align:top;padding-left:8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Taille</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ no_of_employees or '—' }}</p>
                      </td></tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          {% if activite_autres %}
          <tr>
            <td style="padding-bottom:8px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                <tr><td style="padding:16px 16px 4px;">
                  <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Autres activités</p>
                </td></tr>
                <tr><td style="padding:4px 16px 16px;">
                  <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ activite_autres }}</p>
                </td></tr>
              </table>
            </td>
          </tr>
          {% endif %}

        </table>


        <!-- ─── SECTION : Modules Demandés ─── -->
        {% if has_modules %}
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:32px;">

          <tr>
            <td style="padding-bottom:14px;border-bottom:2px solid #F32A57;">
              <p style="margin:0;font-size:15px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#032A5F;text-transform:uppercase;letter-spacing:0.8px;">
                &#128230;&nbsp; Modules Demandés
              </p>
            </td>
          </tr>
          <tr><td style="padding-bottom:16px;font-size:1px;line-height:1px;">&nbsp;</td></tr>

          <!-- Badges modules — chaque badge dans sa propre <td> inline -->
          <tr>
            <td>
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="padding:0 8px 10px 0;">
                    <!-- On liste les badges actifs séparés par des espaces insécables -->
                    {% if m_compta %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Comptabilité &amp; Finance</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_immob %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Immobilisation</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_achats %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Achats</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_stocks %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Gestion des Stocks</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_ventes %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Ventes &amp; CRM</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_pos %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Point de vente</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_rh %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">RH &amp; Paie</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_prod %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Production</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_qual %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Qualité</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_projet %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Projet</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if m_support %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#F32A57;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Support</span>
                      </td></tr>
                    </table>
                    {% endif %}
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
        {% endif %}


        <!-- ─── SECTION : Données à Migrer ─── -->
        {% if has_migration %}
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:32px;">

          <tr>
            <td style="padding-bottom:14px;border-bottom:2px solid #F32A57;">
              <p style="margin:0;font-size:15px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#032A5F;text-transform:uppercase;letter-spacing:0.8px;">
                &#128260;&nbsp; Données à Migrer
              </p>
            </td>
          </tr>
          <tr><td style="padding-bottom:16px;font-size:1px;line-height:1px;">&nbsp;</td></tr>

          <tr>
            <td>
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="padding:0 8px 10px 0;">
                    {% if mig_clients %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#0756C5;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Clients</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if mig_fournisseurs %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#0756C5;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Fournisseurs</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if mig_produits %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#0756C5;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Produits/Services</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if mig_factures %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#0756C5;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Factures</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if mig_stocks %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#0756C5;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Stocks</span>
                      </td></tr>
                    </table>
                    {% endif %}
                    {% if mig_salaries %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="display:inline-table;margin:0 6px 8px 0;">
                      <tr><td style="background:#0756C5;border-radius:24px;padding:8px 14px;">
                        <span style="font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#ffffff;white-space:nowrap;">Salariés</span>
                      </td></tr>
                    </table>
                    {% endif %}
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          {% if autres %}
          <tr>
            <td style="padding-top:10px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                <tr><td style="padding:16px 16px 4px;">
                  <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Autres données</p>
                </td></tr>
                <tr><td style="padding:4px 16px 16px;">
                  <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ autres }}</p>
                </td></tr>
              </table>
            </td>
          </tr>
          {% endif %}

        </table>
        {% endif %}


        <!-- ─── SECTION : Contexte Actuel ─── -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:32px;">

          <tr>
            <td style="padding-bottom:14px;border-bottom:2px solid #F32A57;">
              <p style="margin:0;font-size:15px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#032A5F;text-transform:uppercase;letter-spacing:0.8px;">
                &#128421;&nbsp; Contexte Actuel
              </p>
            </td>
          </tr>
          <tr><td style="padding-bottom:16px;font-size:1px;line-height:1px;">&nbsp;</td></tr>

          <!-- Solution existante + Si oui laquelle -->
          <tr>
            <td style="padding-bottom:14px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td width="49%" style="vertical-align:top;padding-right:8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Solution existante</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ logiciel or '—' }}</p>
                      </td></tr>
                    </table>
                  </td>
                  <td width="2%">&nbsp;</td>
                  <td width="49%" style="vertical-align:top;padding-left:8px;">
                    {% if si_oui_laquelle %}
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Si oui, laquelle</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ si_oui_laquelle }}</p>
                      </td></tr>
                    </table>
                    {% endif %}
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Cahier de charge + Stade -->
          <tr>
            <td style="padding-bottom:8px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td width="49%" style="vertical-align:top;padding-right:8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Cahier de charge</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ have_cahier or '—' }}</p>
                      </td></tr>
                    </table>
                  </td>
                  <td width="2%">&nbsp;</td>
                  <td width="49%" style="vertical-align:top;padding-left:8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #F32A57;">
                      <tr><td style="padding:16px 16px 4px;">
                        <p style="margin:0;font-size:11px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#F32A57;text-transform:uppercase;letter-spacing:0.6px;">Stade du projet</p>
                      </td></tr>
                      <tr><td style="padding:4px 16px 16px;">
                        <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:600;color:#032A5F;">{{ stade or '—' }}</p>
                      </td></tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>


        <!-- ─── SECTION : Besoin Exprimé ─── -->
        {% if besoin %}
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:32px;">

          <tr>
            <td style="padding-bottom:14px;border-bottom:2px solid #F32A57;">
              <p style="margin:0;font-size:15px;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-weight:700;color:#032A5F;text-transform:uppercase;letter-spacing:0.8px;">
                &#128221;&nbsp; Besoin Exprimé
              </p>
            </td>
          </tr>
          <tr><td style="padding-bottom:16px;font-size:1px;line-height:1px;">&nbsp;</td></tr>

          <tr>
            <td>
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f0f4f8;border-radius:10px;border-left:4px solid #0756C5;">
                <tr><td style="padding:20px 24px;">
                  <p style="margin:0;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#032A5F;line-height:1.7;mso-line-height-rule:exactly;">{{ besoin }}</p>
                </td></tr>
              </table>
            </td>
          </tr>

        </table>
        {% endif %}


        <!-- ─── CTA — Gradient via VML ─── -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-bottom:10px;">
          <tr>
            <td style="border-radius:12px;overflow:hidden;padding:0;text-align:center;">

              <!--[if mso]>
              <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width:540px;border-radius:12px;">
                <v:fill type="gradient" color="#F32A57" color2="#0756C5" angle="135"/>
                <v:textbox inset="30px,28px,30px,28px" style="mso-fit-shape-to-text:true;">
              <![endif]-->

              <div style="background:linear-gradient(135deg,#F32A57 0%,#0756C5 100%);border-radius:12px;padding:30px;text-align:center;">
                <p style="margin:0 0 18px;font-size:14px;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#ffffff;mso-line-height-rule:exactly;">
                  Accéder au détail complet du prospect
                </p>

                <!--[if mso]>
                <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
                  href="{{ doc.get_url() }}"
                  style="height:44px;v-text-anchor:middle;width:220px;" arcsize="15%"
                  strokecolor="#ffffff" fillcolor="#ffffff">
                  <w:anchorlock/>
                  <center style="color:#F32A57;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;">
                    Voir le Lead Complet &#8594;
                  </center>
                </v:roundrect>
                <![endif]-->
                <!--[if !mso]><!-->
                <a href="{{ doc.get_url() }}" target="_blank"
                   style="display:inline-block;background:#ffffff;color:#F32A57;font-family:Segoe UI,Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;text-decoration:none;border-radius:8px;padding:13px 34px;">
                  Voir le Lead Complet &rarr;
                </a>
                <!--<![endif]-->
              </div>

              <!--[if mso]>
                </v:textbox>
              </v:rect>
              <![endif]-->

            </td>
          </tr>
        </table>


      </td>
    </tr>

    <!-- ══════════════════════════════════════
         FOOTER
    ══════════════════════════════════════ -->
    <tr>
      <td style="background:#f0f4f8;padding:22px 30px;text-align:center;border-top:1px solid #e8eef8;">
        <p style="margin:0 0 6px;font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#0756C5;">
          &#128202;&nbsp; Lead ID&nbsp;: <strong>{{ doc.name }}</strong>
        </p>
        <p style="margin:0;font-size:12px;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#6b7280;">
          Cette demande a été reçue via le formulaire de prospect ERPNext
        </p>
      </td>
    </tr>

  </table>
  <!-- /Card -->

</td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->

</body>
</html>