"""
Script to fix account 401 - set it to Balance Sheet instead of Profit and Loss
Run this in the ERPNext console or as a custom script
"""
import frappe

def fix_account_401(company=None):
	"""
	Update account 401 to have root_type=Liability and report_type=Balance Sheet
	"""
	if not company:
		# Get the first company if not specified
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			frappe.throw("No company found. Please specify a company.")
	
	# Find account 401
	account_name = frappe.db.get_value(
		"Account", 
		{"company": company, "account_number": "401"}, 
		"name"
	)
	
	if not account_name:
		frappe.throw(f"Account 401 not found for company {company}")
	
	# Get current values
	current_root = frappe.db.get_value("Account", account_name, "root_type")
	current_report = frappe.db.get_value("Account", account_name, "report_type")
	
	frappe.msgprint(f"Current values for account 401:")
	frappe.msgprint(f"  Root Type: {current_root}")
	frappe.msgprint(f"  Report Type: {current_report}")
	
	# Update the account
	account = frappe.get_doc("Account", account_name)
	account.root_type = "Liability"
	account.report_type = "Balance Sheet"
	account.save()
	
	frappe.msgprint(f"Account 401 updated successfully!")
	frappe.msgprint(f"  New Root Type: {account.root_type}")
	frappe.msgprint(f"  New Report Type: {account.report_type}")
	
	return account_name

if __name__ == "__main__":
	fix_account_401()

