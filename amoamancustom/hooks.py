app_name = "amoamancustom"
app_title = "Amoaman Custom App"
app_publisher = "KONE Fousseni"
app_description = "custom amoaman erpnet app"
app_email = "fkone@amoaman.com"
app_license = "mit"

from hrms.hr.doctype.expense_claim import expense_claim
from amoamancustom.overrides.expense_claim import get_total_reimbursed_amount

# Patch de la fonction originale
expense_claim.get_total_reimbursed_amount = get_total_reimbursed_amount

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "amoamancustom",
# 		"logo": "/assets/amoamancustom/logo.png",
# 		"title": "Amoaman Custom App",
# 		"route": "/amoamancustom",
# 		"has_permission": "amoamancustom.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/amoamancustom/css/amoamancustom.css"
# app_include_js = "/assets/amoamancustom/js/amoamancustom.js"

# include js, css files in header of web template
# web_include_css = "/assets/amoamancustom/css/amoamancustom.css"
# web_include_js = "/assets/amoamancustom/js/amoamancustom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "amoamancustom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Timesheet" : "public/js/timesheet/timesheet.js",
    "Sales Order" : "public/js/sales_order/sales_order.js",
    "Quotation" : "public/js/quotation/quotation.js",
    "Project" : "public/js/project/project.js",
    "Employee" : "public/js/employee/employee.js",
    "Salary Slip" : "public/js/salary_slip/salary_slip.js",
    "Salary Structure Assignment" : "public/js/salary_structure _assignment/salary_structure _assignment.js"
    }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "amoamancustom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
    "methods": [
        "amoamancustom.utils.timesheet_utils.build_time_log_rows",
    ],
    # Si vous voulez exposer des filtres custom :
    # "filters": ["amoamancustom.utils.some_module.some_filter"],
}

# Installation
# ------------

# before_install = "amoamancustom.install.before_install"
# after_install = "amoamancustom.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "amoamancustom.uninstall.before_uninstall"
# after_uninstall = "amoamancustom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "amoamancustom.utils.before_app_install"
# after_app_install = "amoamancustom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "amoamancustom.utils.before_app_uninstall"
# after_app_uninstall = "amoamancustom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "amoamancustom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Employee": {
		"on_update": "amoamancustom.hr_custom.doctype.employee.employee.employment_type_changed",
	},
   #"Sales Invoice" :{
	   #"before_save" : "amoamancustom.hr_custom.doctype.sales_invoice.sales_invoice.before_submit_link_so_items"
   #}
}



# Scheduled Tasks
# ---------------
scheduler_events = {
 	"all": [
 		#"amoamancustom.tasks.all"
 	],
 	"daily": [
 		"amoamancustom.schedulers.employee.set_seniority"
 	],
 	"hourly": [
 		#"amoamancustom.tasks.hourly"
 	],
 	"weekly": [
 		#"amoamancustom.tasks.weekly"
 	],
 	"monthly": [
 		#"amoamancustom.schedulers.employee.set_seniority"
 	],
 }

# Testing
# -------

# before_tests = "amoamancustom.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "amoamancustom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "amoamancustom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["amoamancustom.utils.before_request"]
# after_request = ["amoamancustom.utils.after_request"]

# Job Events
# ----------
# before_job = ["amoamancustom.utils.before_job"]
# after_job = ["amoamancustom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"amoamancustom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


fixtures = [
    # -----------------------------
    # 1. Custom Fields
    # -----------------------------
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt", "in", [
                    # --- Département RH ---
                    "Employee",
                    "Employment Contract",
                    "Employee Grade",
                    "Expense Claim",
                    "Timesheet",
                    "Attendance",
                    "Leave Application",
                    "Leave Allocation",
                    "Payroll Entry",
                    "Salary Slip",
                    "Shift Assignment",
                    "Department",
                    "Designation",

                    # --- Département Comptabilité / Finance ---
                    "Item",
                    "Sales Invoice",
                    "Purchase Invoice",
                    "Sales Order",
                    "Purchase Order",
                    "Quotation",
                    "Delivery Note",
                    "Purchase Receipt",
                    "Payment Entry",
                    "Customer",
                    "Supplier",
                    "Contact",
                    "Address",
                    "Contract",
                    "Journal Entry",
                    "Account",
                    "Cost Center",
                    "Company",
                    "Tax Rule",
                    "Pricing Rule",

                    # --- Autres DocTypes fréquemment utilisés ---
                    "Project",
                    "Task",
                    "Issue",
                    "Stock Entry",
                    "Warehouse",
                    "Batch",
                    "Serial No",
                    "Material Request",
                    "Work Order",
                    "BOM",
                    "Subscription",
                    "Email Template",
                    "Notification Log",
                    "File",
                    "Web Page",
                    "Website Settings",
                    "Communication",
                    "ToDo"
                ]
            ]
        ]
    },

    # -----------------------------
    # 2. Property Setters
    # -----------------------------
    {
        "doctype": "Property Setter",
        "filters": [
            [
                "doc_type", "in", [
                    # --- Département RH ---
                    "Employee",
                    "Employment Contract",
                    "Employee Grade",
                    "Expense Claim",
                    "Timesheet",
                    "Attendance",
                    "Leave Application",
                    "Leave Allocation",
                    "Payroll Entry",
                    "Salary Slip",
                    "Shift Assignment",
                    "Department",
                    "Designation",

                    # --- Département Comptabilité / Finance ---
                    "Item",
                    "Sales Invoice",
                    "Purchase Invoice",
                    "Sales Order",
                    "Purchase Order",
                    "Quotation",
                    "Delivery Note",
                    "Purchase Receipt",
                    "Payment Entry",
                    "Customer",
                    "Supplier",
                    "Contact",
                    "Address",
                    "Contract",
                    "Journal Entry",
                    "Account",
                    "Cost Center",
                    "Company",
                    "Tax Rule",
                    "Pricing Rule",

                    # --- Autres DocTypes utilisés ---
                    "Project",
                    "Task",
                    "Issue",
                    "Stock Entry",
                    "Warehouse",
                    "Batch",
                    "Serial No",
                    "Material Request",
                    "Work Order",
                    "BOM",
                    "Subscription",
                    "Email Template",
                    "Notification Log",
                    "File",
                    "Web Page",
                    "Website Settings",
                    "Communication",
                    "ToDo"
                ]
            ]
        ]
    },

    # -----------------------------
    # 3. Workflows
    # -----------------------------
    {
        "doctype": "Workflow",
        "filters": [
            [
                "document_type", "in", [
                    # RH
                    "Employee",
                    "Employment Contract",
                    "Expense Claim",
                    "Timesheet",
                    "Leave Application",
                    "Payroll Entry",
                    "Salary Slip",

                    # Comptabilité
                    "Sales Invoice",
                    "Purchase Invoice",
                    "Sales Order",
                    "Purchase Order",
                    "Quotation",
                    "Delivery Note",
                    "Payment Entry",
                    "Journal Entry",

                    # Stock
                    "Stock Entry",
                    "Material Request",
                    "Work Order",

                    # Contacts et adresses
                    "Address",
                    "Contact"
                ]
            ]
        ]
    },

    # -----------------------------
    # 4. Workflow States
    # -----------------------------
    {
        "doctype": "Workflow State",
        "filters": [
            [
                "workflow_state_name", "not like", "%Recruitment%"
            ]
        ]
    },

    # -----------------------------
    # 5. Workflow Actions
    # -----------------------------
    {
        "doctype": "Workflow Action",
        "filters": [
            [
                "name", "not like", "%Recruitment%"
            ]
        ]
    },

    # -----------------------------
    # 6. Roles (incluant RH + Comptabilité)
    # -----------------------------
    {
        "doctype": "Role",
        "filters": [
            [
                "name", "in", [
                    # RH
                    "HR Manager",
                    "HR User",
                    "Employee",
                    "Leave Approver",
                    "Expense Approver",
                    "Payroll Manager",
                    "Timesheet Approver",

                    # Comptabilité
                    "Accounts Manager",
                    "Accounts User",
                    "Auditor",
                    "Stock Manager",
                    "Stock User",
                    "Sales Manager",
                    "Sales User",
                    "Purchase Manager",
                    "Purchase User",

                    # Autres
                    "System Manager",
                    "Administrator",
                    "Project Manager",
                    "Project User"
                ]
            ]
        ]
    },

    # -----------------------------
    # 7. Print Formats
    # -----------------------------
    {
        "doctype": "Print Format",
        "filters": [
            [
                "doc_type", "in", [
                    # RH
                    "Employee",
                    "Employment Contract",
                    "Expense Claim",
                    "Timesheet",
                    "Salary Slip",

                    # Comptabilité
                    "Sales Invoice",
                    "Purchase Invoice",
                    "Quotation",
                    "Sales Order",
                    "Purchase Order",
                    "Delivery Note",
                    "Purchase Receipt",
                    "Payment Entry",
                    "Journal Entry",
                    "Address",
                    "Contact",

                    # Autres
                    "Project",
                    "Task",
                    "Stock Entry",
                    "Material Request",
                    "Work Order"
                ]
            ]
        ]
    },

    # -----------------------------
    # 8. Reports personnalisés
    # -----------------------------
    {
        "doctype": "Report",
        "filters": [
            [
                "ref_doctype", "in", [
                    # RH
                    "Employee",
                    "Employment Contract",
                    "Expense Claim",
                    "Timesheet",
                    "Leave Application",
                    "Payroll Entry",
                    "Salary Slip",

                    # Comptabilité
                    "Sales Invoice",
                    "Purchase Invoice",
                    "Quotation",
                    "Sales Order",
                    "Purchase Order",
                    "Delivery Note",
                    "Purchase Receipt",
                    "Payment Entry",
                    "Journal Entry",
                    "Account",
                    "Cost Center",
                    "Company",
                    "Address",
                    "Contact",

                    # Autres
                    "Project",
                    "Task",
                    "Stock Entry",
                    "Material Request",
                    "Work Order"
                ]
            ]
        ]
    }
]




