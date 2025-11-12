# about.py
import frappe

def get_context(context):
    
    context.partners = frappe.get_all("Partner", fields = "*")
    return context