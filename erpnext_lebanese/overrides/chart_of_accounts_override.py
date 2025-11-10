# erpnext_lebanese/overrides/chart_of_accounts_override.py
import frappe, json, os
from frappe import _
from frappe.utils import cstr

@frappe.whitelist()
def get_lebanese_charts(country=None, with_standard=False):
    """
    Return Lebanese charts - now uses ERPNext's standard method
    The chart JSON is copied to ERPNext's unverified folder during installation
    """
    # Enable unverified charts so ERPNext can find our chart
    frappe.local.flags.allow_unverified_charts = True
    
    # Use ERPNext's standard method to get charts for Lebanon
    from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import get_charts_for_country
    
    country = country or "Lebanon"
    charts = get_charts_for_country(country, with_standard=with_standard)
    
    # Filter to only return Lebanese charts, or return all if none found
    lebanese_charts = [c for c in charts if "Lebanese" in c or "lebanese" in c.lower()]
    
    return lebanese_charts if lebanese_charts else charts

@frappe.whitelist()
def get_lebanese_coa(doctype, parent, is_root=None, chart=None):
    """
    Get Lebanese Chart of Accounts - uses ERPNext's standard method
    The chart JSON is in ERPNext's unverified folder
    """
    # Enable unverified charts so ERPNext can find our chart
    frappe.local.flags.allow_unverified_charts = True
    
    # Use ERPNext's standard method
    from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import get_chart
    
    chart = chart if chart else frappe.flags.chart
    frappe.flags.chart = chart
    
    parent = None if parent == _("All Accounts") else parent
    
    # Get chart tree from ERPNext's standard method
    chart_tree = get_chart(chart)
    
    if not chart_tree:
        return []
    
    # Build account list from tree
    accounts = []
    
    def _build_accounts(children, parent_account):
        for account_name, child in children.items():
            if account_name not in [
                "account_name", "account_number", "account_type", 
                "root_type", "is_group", "tax_rate", "account_currency"
            ]:
                account = {}
                account["parent_account"] = parent_account
                account["expandable"] = identify_is_group(child)
                account["value"] = (
                    (cstr(child.get("account_number")).strip() + " - " + account_name)
                    if child.get("account_number")
                    else account_name
                )
                accounts.append(account)
                _build_accounts(child, account["value"])
    
    _build_accounts(chart_tree, parent)
    
    # Filter to show data for the selected node only
    filtered_accounts = [d for d in accounts if d["parent_account"] == parent]
    
    return filtered_accounts

# Removed - now using ERPNext's standard get_chart method

def identify_is_group(child):
    """Identify if account is a group account"""
    if isinstance(child, dict):
        return child.get("is_group", 1 if any(key not in [
            "account_name", "account_number", "account_type", 
            "root_type", "is_group", "tax_rate", "account_currency"
        ] for key in child.keys()) else 0)
    return False

# Removed - ERPNext handles chart installation from JSON file in unverified folder
