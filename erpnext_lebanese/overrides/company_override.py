# erpnext_lebanese/overrides/company_override.py
import frappe
from frappe import _
from erpnext.setup.doctype.company.company import Company


class LebaneseCompany(Company):
	"""
	Override Company class to install Lebanese chart of accounts
	This intercepts the create_default_accounts method and on_update
	"""
	
	def on_update(self):
		"""
		Override on_update to handle Lebanese companies properly
		Skip tax template creation for Lebanese companies as they have different tax structure
		CRITICAL: Set allow_unverified_charts BEFORE calling super().on_update() so get_chart() can find our chart
		"""
		# Check if this is a Lebanese company - check both instance and database
		country = getattr(self, 'country', None)
		chart_of_accounts = getattr(self, 'chart_of_accounts', None)
		
		# If not available on instance, check database
		if not country and self.name:
			try:
				country = frappe.db.get_value("Company", self.name, "country")
				chart_of_accounts = frappe.db.get_value("Company", self.name, "chart_of_accounts")
			except:
				pass
		
		is_lebanese = (country == "Lebanon" and chart_of_accounts and 
		              ("Lebanese" in chart_of_accounts or "lebanese" in chart_of_accounts.lower()))
		
		if is_lebanese:
			# CRITICAL: Enable unverified charts BEFORE calling super().on_update()
			# This ensures get_chart() can find our Lebanese chart in the unverified folder
			frappe.local.flags.allow_unverified_charts = True
			
			# Set flag to skip tax template creation - set it on the instance too for safety
			frappe.flags.skip_tax_template_for_lebanese = True
			if not hasattr(self, 'flags'):
				self.flags = frappe._dict()
			self.flags.skip_tax_template_for_lebanese = True
		
		try:
			# Call parent on_update - this will call create_default_accounts() which calls get_chart()
			super().on_update()
		finally:
			# Clear the flags
			if is_lebanese:
				frappe.flags.skip_tax_template_for_lebanese = False
				if hasattr(self, 'flags'):
					self.flags.skip_tax_template_for_lebanese = False
				# Don't clear allow_unverified_charts - it might be needed elsewhere
	
	def create_default_tax_template(self):
		"""
		Override to skip tax template creation for Lebanese companies
		Lebanon has different tax structure, so we skip the default ERPNext tax setup
		"""
		# ALWAYS check if this is a Lebanese company first
		# Check instance attributes
		country = getattr(self, 'country', None)
		chart_of_accounts = getattr(self, 'chart_of_accounts', None)
		
		# If not available, check database
		if not country and self.name:
			try:
				country = frappe.db.get_value("Company", self.name, "country")
				chart_of_accounts = frappe.db.get_value("Company", self.name, "chart_of_accounts")
			except:
				pass
		
		is_lebanese_company = (country == "Lebanon" and chart_of_accounts and 
		                      ("Lebanese" in chart_of_accounts or "lebanese" in chart_of_accounts.lower()))
		
		# Also check flags
		is_lebanese_flag = getattr(frappe.flags, 'skip_tax_template_for_lebanese', False)
		is_lebanese_instance = getattr(self.flags, 'skip_tax_template_for_lebanese', False) if hasattr(self, 'flags') else False
		
		if is_lebanese_flag or is_lebanese_instance or is_lebanese_company:
			return
		
		# For non-Lebanese companies, use default behavior
		super().create_default_tax_template()
	
	def create_default_accounts(self):
		"""
		Override create_default_accounts - ERPNext will handle chart installation naturally
		from the JSON file we copied to the unverified folder
		We just need to ensure default accounts are set after installation
		"""
		# CRITICAL: Enable unverified charts FIRST - this must be set before create_charts is called
		frappe.local.flags.allow_unverified_charts = True
		
		# Check if this is a Lebanese company
		country = getattr(self, 'country', None)
		chart_of_accounts = getattr(self, 'chart_of_accounts', None)
		
		# If not available on instance, check database
		if not country and self.name:
			try:
				country = frappe.db.get_value("Company", self.name, "country")
				chart_of_accounts = frappe.db.get_value("Company", self.name, "chart_of_accounts")
			except:
				pass
		
		is_lebanese = (country == "Lebanon" and chart_of_accounts and 
		              ("Lebanese" in chart_of_accounts or "lebanese" in chart_of_accounts.lower()))
		
		# Let ERPNext handle chart installation normally
		# It will find our Lebanese chart in the unverified folder
		try:
			super().create_default_accounts()
		except Exception as e:
			raise
		
		# After chart installation, set default accounts for Lebanese companies
		if self.country == "Lebanon" and self.chart_of_accounts:
			chart_name = self.chart_of_accounts or ""
			if "Lebanese" in chart_name or "lebanese" in chart_name.lower():
				try:
					# Set default accounts after chart installation
					set_lebanese_default_accounts(self.name)
					frappe.db.commit()
				except Exception as e:
					# Don't fail - accounts are already created
					pass


# Removed - ERPNext will handle chart installation from the JSON file in unverified folder


def set_lebanese_default_accounts(company):
	"""Set default accounts for Lebanese company after chart installation"""
	company_doc = frappe.get_doc("Company", company)
	
	# Set basic default accounts
	defaults = {
		"default_receivable_account": frappe.db.get_value(
			"Account", 
			{"company": company, "account_type": "Receivable", "is_group": 0},
			order_by="creation asc"
		),
		"default_payable_account": frappe.db.get_value(
			"Account", 
			{"company": company, "account_type": "Payable", "is_group": 0},
			order_by="creation asc"
		),
	}
	
	# Set cash account if exists
	cash_account = frappe.db.get_value(
		"Account",
		{"company": company, "account_type": "Cash", "is_group": 0},
		order_by="creation asc"
	)
	if cash_account:
		defaults["default_cash_account"] = cash_account
	
	# Set bank account if exists
	bank_account = frappe.db.get_value(
		"Account",
		{"company": company, "account_type": "Bank", "is_group": 0},
		order_by="creation asc"
	)
	if bank_account:
		defaults["default_bank_account"] = bank_account
	
	# Update company with defaults
	for field, value in defaults.items():
		if value:
			company_doc.db_set(field, value)

