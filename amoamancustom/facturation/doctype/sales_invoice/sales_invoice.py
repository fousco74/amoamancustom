import frappe
from frappe.utils import flt

def before_submit_link_so_items(doc, method=None):
    # Ne traite pas les retours / factures sans projet
    if getattr(doc, "is_return", 0) or not getattr(doc, "project", None):
        return

    # Récupère la SO depuis le Projet
    sales_order = frappe.db.get_value("Project", doc.project, "sales_order")
    if not sales_order:
        return  # rien à lier

    # Récupère les lignes de SO (docstatus=1) avec montants et déjà facturé
    so_items = frappe.get_all(
        "Sales Order Item",
        filters={"parent": sales_order, "docstatus": 1},
        fields=["name", "item_code", "project", "amount", "billed_amt"]
    )

    if not so_items:
        return

    def remaining(row):
        return flt(row.get("amount")) - flt(row.get("billed_amt"))

    def pick_so_item(si_item):
        # 1) même item_code & même projet
        cands = [r for r in so_items
                 if r.get("item_code") == si_item.item_code and r.get("project") == doc.project]
        # 2) sinon même item_code
        if not cands:
            cands = [r for r in so_items if r.get("item_code") == si_item.item_code]
        # 3) sinon même projet
        if not cands:
            cands = [r for r in so_items if r.get("project") == doc.project]
        if not cands:
            return None
        # Choisit celle avec le plus de reste à facturer
        cands.sort(key=lambda r: remaining(r), reverse=True)
        for row in cands:
            if remaining(row) > 0:
                return row
        # si toutes “pleines”, retourne la première (ERPNext lèvera l’overflow si ça dépasse)
        return cands[0]

    for it in doc.get("items", []):
        # ne pas écraser un lien déjà présent
        if getattr(it, "sales_order", None) and getattr(it, "so_detail", None):
            continue

        it.sales_order = sales_order

        if not getattr(it, "so_detail", None):
            match = pick_so_item(it)
            if match:
                it.so_detail = match["name"]
                

