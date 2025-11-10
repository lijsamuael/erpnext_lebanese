import frappe
from frappe import _
from frappe.utils import nowdate
import json

from erpnext.setup.setup_wizard.operations import install_fixtures as fixtures

def after_install():
    """Called after app installation"""
    pass

def get_setup_stages(args=None):
    """
    Override ERPNext's get_setup_stages to include Lebanese setup
    The company creation will automatically trigger chart installation via doc_events hook
    """
    
    # Parse args if it's a string
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except:
            args = {}
    elif args is None:
            args = {}
    
    if frappe.db.sql("select name from tabCompany"):
        # Company already exists, just wrap up
        stages = [
            {
                "status": _("Wrapping up"),
                "fail_msg": _("Failed to login"),
                "tasks": [{"fn": fin, "args": args, "fail_msg": _("Failed to login")}],
            }
        ]
    else:
        # No company exists, run full setup
        # The company creation will automatically install Lebanese chart via doc_events hook
        stages = [
            {
                "status": _("Installing presets"),
                "fail_msg": _("Failed to install presets"),
                "tasks": [{"fn": stage_fixtures, "args": args, "fail_msg": _("Failed to install presets")}],
            },
            {
                "status": _("Setting up company"),
                "fail_msg": _("Failed to setup company"),
                "tasks": [{"fn": setup_company, "args": args, "fail_msg": _("Failed to setup company")}],
            },
            {
                "status": _("Setting defaults"),
                "fail_msg": "Failed to set defaults",
                "tasks": [
                    {"fn": setup_defaults, "args": args, "fail_msg": _("Failed to setup defaults")},
                ],
            },
            {
                "status": _("Wrapping up"),
                "fail_msg": _("Failed to login"),
                "tasks": [{"fn": fin, "args": args, "fail_msg": _("Failed to login")}],
            },
        ]

    return stages

def stage_fixtures(args):
    """Install fixtures - we'll use ERPNext's but can override if needed"""
    from erpnext.setup.setup_wizard.operations import install_fixtures as fixtures
    
    # Parse args if it's a string
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except:
            args = {}
    
    # Get country from args or use Lebanon as default for Lebanese setup
    country = None
    if isinstance(args, dict):
        country = args.get("country")
        
        # If no country specified but this is a Lebanese setup, default to Lebanon
        if not country:
            chart_of_accounts = args.get('chart_of_accounts', '')
            if 'Lebanon' in chart_of_accounts or 'lebanese' in chart_of_accounts.lower():
                country = "Lebanon"
    
    # If still no country, use a safe default
    if not country:
        country = "United States"  # ERPNext's default
    
    fixtures.install(country)

def setup_company(args):
	"""
	Setup company - ERPNext will automatically find and install the Lebanese chart
	from the JSON file in the unverified folder. We just ensure country is set correctly.
	"""
	# CRITICAL: Enable unverified charts FIRST, before any company creation
	# This must be set at the start so it's available when make_records creates the company
	frappe.local.flags.allow_unverified_charts = True
        
	# Parse args if it's a string
	if isinstance(args, str):
		try:
			args = json.loads(args)
		except:
			args = {}
	elif args is None:
            args = {}
        
	# Convert to dict if not already
	if not isinstance(args, dict):
		args = dict(args) if hasattr(args, '__dict__') else {}
	
	# Convert to frappe._dict for consistent access
	args_dict = frappe._dict(args)
	
	# Ensure country is set to Lebanon for Lebanese chart
	chart_of_accounts = args_dict.get('chart_of_accounts', '')
	is_lebanese = chart_of_accounts and ('Lebanese' in chart_of_accounts or 'lebanese' in chart_of_accounts.lower())
	
	# ALWAYS set country to Lebanon if Lebanese chart is selected
	if is_lebanese:
		args_dict['country'] = 'Lebanon'
		if not args_dict.get('currency'):
			args_dict['currency'] = 'LBP'
	
	# Also ensure country is set even if chart name doesn't match exactly
	if not args_dict.get('country'):
		args_dict['country'] = 'Lebanon'
	
	# Use ERPNext's standard install_company - it will find the chart automatically
	# The LebaneseCompany override will handle tax template skipping
	try:
		fixtures.install_company(args_dict)
        frappe.db.commit()
    except Exception as e:
        frappe.db.rollback()
		raise
	
	# Verify company was created
	try:
		company_name = args_dict.get('company_name')
		if company_name:
			company_exists = frappe.db.exists("Company", company_name)
			if not company_exists:
				raise Exception(f"Company {company_name} was not created")
    except Exception as e:
		frappe.db.rollback()
        raise

def setup_defaults(args):
	"""Setup defaults - this runs after company creation"""
	# Ensure args is a dict
	if isinstance(args, str):
		try:
			args = json.loads(args)
		except:
			args = {}
	elif args is None:
		args = {}
	
	fixtures.install_defaults(frappe._dict(args))
 
def fin(args):
    """Final setup tasks"""
    frappe.local.message_log = []
    
    # Parse args if it's a string
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except:
            args = {}
    elif args is None:
            args = {}
    
    login_as_first_user(args)

def setup_demo(args):
    """Setup demo data if requested"""
    # Parse args if it's a string
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except:
            args = {}
    elif args is None:
            args = {}
    
    if isinstance(args, dict) and args.get("setup_demo"):
        from erpnext.setup.demo import setup_demo_data
        frappe.enqueue(setup_demo_data, enqueue_after_commit=True, at_front=True)

def login_as_first_user(args):
    """Login as first user"""
    if isinstance(args, dict) and args.get("email") and hasattr(frappe.local, "login_manager"):
        frappe.local.login_manager.login_as(args.get("email"))

@frappe.whitelist()
def setup_complete(args=None):
    """
    Programmatic setup complete - override ERPNext's method
    This is called via API, so args might be a JSON string
    """
    # Parse args if it's a string and convert to dict
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except:
            args = {}
    elif args is None:
        args = {}
    
    # Ensure default_currency is set for Lebanese setup
    if isinstance(args, dict):
        chart_of_accounts = args.get('chart_of_accounts', '')
        if 'Lebanese' in chart_of_accounts or 'lebanese' in chart_of_accounts.lower():
    if not args.get('currency'):
                args['currency'] = 'LBP'  # Set Lebanese Pound as default
            if not args.get('country'):
                args['country'] = 'Lebanon'
    
    try:
        # Run setup stages - company creation will trigger chart installation via hook
            stage_fixtures(args)
            setup_company(args)
            setup_defaults(args)
            fin(args)
            
            # Return exactly what the frontend expects
            return {
                "status": "success",
                "message": "Setup Completed",
                "home_page": "/desk"
            }
            
    except Exception as e:
        frappe.db.rollback()
        return {
            "status": "error",
            "message": str(e)
        }
    





