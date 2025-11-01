# erpnext_lebanese/overrides/chart_of_accounts_override.py
import frappe, json, os
from frappe import _
from frappe.utils import cstr

@frappe.whitelist()
def get_lebanese_charts(country=None, with_standard=False):
    """Return only the Lebanese Standard chart"""
    path = frappe.get_app_path("erpnext_lebanese", "data", "chart_of_accounts", "lebanese_standard.json")
    if os.path.exists(path):
        with open(path) as f:
            content = json.load(f)
            if content and content.get("disabled", "No") == "No":
                return [content["name"]]
    return []

@frappe.whitelist()
def get_lebanese_coa(doctype, parent, is_root=None, chart=None):
    """Get Lebanese Chart of Accounts from custom JSON file"""
    
    # Add chart to flags to retrieve when called from expand all function
    chart = chart if chart else frappe.flags.chart
    frappe.flags.chart = chart
    
    parent = None if parent == _("All Accounts") else parent
    
    # Build tree from your custom JSON file
    accounts = build_tree_from_lebanese_json()
    
    # Filter out to show data for the selected node only
    accounts = [d for d in accounts if d["parent_account"] == parent]
    
    return accounts

def build_tree_from_lebanese_json():
    """Build account tree from Lebanese standard JSON file"""
    accounts = []
    
    # Get the chart data from your custom path
    chart_data = get_lebanese_chart()
    
    if not chart_data:
        return accounts
    
    def _import_accounts(children, parent):
        """Recursively build account tree"""
        for account_name, child in children.items():
            # Skip metadata fields
            if account_name in [
                "account_name", "account_number", "account_type", 
                "root_type", "is_group", "tax_rate", "account_currency"
            ]:
                continue
            
            account = {}
            account["parent_account"] = parent
            account["expandable"] = identify_is_group(child)
            account["value"] = (
                (cstr(child.get("account_number")).strip() + " - " + account_name)
                if child.get("account_number")
                else account_name
            )
            accounts.append(account)
            _import_accounts(child, account["value"])
    
    _import_accounts(chart_data, None)
    return accounts

def get_lebanese_chart():
    """Load Lebanese chart from custom path"""
    try:
        # CORRECTED PATH: Use your app path instead of site path
        json_path = frappe.get_app_path("erpnext_lebanese", "data", "chart_of_accounts", "lebanese_standard.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                chart_data = json.load(f)
                return chart_data.get("tree")  # Assuming same structure as ERPNext
        else:
            frappe.msgprint(f"Lebanese COA file not found at: {json_path}")
            return None
    except Exception as e:
        frappe.msgprint(f"Error loading Lebanese COA: {str(e)}")
        return None

def identify_is_group(child):
    """Identify if account is a group account"""
    if isinstance(child, dict):
        return child.get("is_group", 1 if any(key not in [
            "account_name", "account_number", "account_type", 
            "root_type", "is_group", "tax_rate", "account_currency"
        ] for key in child.keys()) else 0)
    return False