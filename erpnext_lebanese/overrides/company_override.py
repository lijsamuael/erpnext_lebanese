# erpnext_lebanese/overrides/company_override.py
import frappe
from frappe import _
from erpnext.setup.doctype.company.company import Company
from erpnext_lebanese.overrides.chart_of_accounts_create_override import (
	create_charts as lebanese_create_charts,
)
from erpnext_lebanese.default_accounts import (
	build_company_structural_defaults,
	build_default_account_map,
)


class LebaneseCompany(Company):
	"""
	Override Company class to install Lebanese chart of accounts
	This intercepts the create_default_accounts method and on_update
	"""
	
	def validate(self):
		"""
		Ensure Lebanese companies default to the Lebanese chart of accounts
		whenever a chart is not explicitly selected. This applies to manual
		company creation after the setup wizard has been completed.
		"""
		# If user is creating a Lebanese company manually and has not selected a chart,
		# default to the Lebanese standard chart that ships with this app.
		if self.country == "Lebanon":
			# Enable loading of charts placed in the unverified folder
			frappe.local.flags.allow_unverified_charts = True

			# Only override when no chart is chosen (or the field is empty/whitespace)
			if not (self.chart_of_accounts or "").strip():
				self.chart_of_accounts = "Lebanese Standard Chart of Accounts"

		# Proceed with the standard validations
		super().validate()

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
		Override create_default_accounts - Use custom create_charts that handles arabic_name and french_name
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
		
		# Use our custom create_charts for Lebanese companies, otherwise use default
		if is_lebanese:
			# Use custom create_charts that handles arabic_name and french_name
			frappe.local.flags.ignore_root_company_validation = True
			lebanese_create_charts(self.name, self.chart_of_accounts, self.existing_company)
			
			# Set default accounts
			self.db_set(
				"default_receivable_account",
				frappe.db.get_value(
					"Account", {"company": self.name, "account_type": "Receivable", "is_group": 0}
				),
			)
			self.db_set(
				"default_payable_account",
				frappe.db.get_value("Account", {"company": self.name, "account_type": "Payable", "is_group": 0}),
			)
			
			# Set additional default accounts for Lebanese companies
			try:
				set_lebanese_default_accounts(self.name)
				frappe.db.commit()
			except Exception as e:
				# Don't fail - accounts are already created
				pass
		else:
			# For non-Lebanese companies, use default behavior
			try:
				super().create_default_accounts()
			except Exception as e:
				raise


# Removed - ERPNext will handle chart installation from the JSON file in unverified folder


def set_lebanese_default_accounts(company):
	"""Ensure all ERPNext default account hooks point to Lebanese chart accounts."""
	account_map = build_default_account_map(company)
	structural_map = build_company_structural_defaults(company)
	updates = {**structural_map, **account_map}
	if updates:
		frappe.db.set_value("Company", company, updates)

