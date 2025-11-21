# erpnext_lebanese/overrides/chart_of_accounts_create_override.py
"""
Override create_charts to handle arabic_name and french_name metadata fields
"""
import frappe
from frappe.utils import cstr
from frappe.utils.nestedset import rebuild_tree
from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
	add_suffix_if_duplicate,
	get_chart
)


def create_charts(
	company, chart_template=None, existing_company=None, custom_chart=None, from_coa_importer=None
):
	"""
	Override create_charts to handle arabic_name and french_name metadata fields
	These fields should be ignored when processing the chart structure
	"""
	chart = custom_chart or get_chart(chart_template, existing_company)
	if chart:
		accounts = []
		metadata_keys = {
			"account_name",
			"account_number",
			"account_type",
			"root_type",
			"is_group",
			"tax_rate",
			"account_currency",
			"arabic_name",
			"french_name",
		}

		def identify_is_group(child):
			if "is_group" in child:
				return child.get("is_group", 0) or 0

			extra_keys = set(child.keys()) - metadata_keys
			return 1 if extra_keys else 0

		def _import_accounts(children, parent, root_type, root_account=False):
			for account_name, child in children.items():
				# Skip metadata keys early
				if account_name in metadata_keys:
					continue

				# Ensure nested structure is a dict (ignore stray values like numbers/strings)
				if not isinstance(child, dict):
					continue

				current_root_type = root_type
				if root_account:
					current_root_type = child.get("root_type", root_type)

				account_number = cstr(child.get("account_number")).strip()
				account_name, account_name_in_db = add_suffix_if_duplicate(
					account_name, account_number, accounts
				)

				is_group = identify_is_group(child)
				report_type = (
					"Balance Sheet"
					if current_root_type in ["Asset", "Liability", "Equity"]
					else "Profit and Loss"
				)

				# Get account_type from child, or set default based on root_type for non-group accounts
				account_type = child.get("account_type")
				if not account_type and current_root_type and not is_group:
					# Set default account_type based on root_type if not specified (only for non-group accounts)
					if current_root_type == "Income":
						account_type = "Income Account"  # Default for Income accounts
					elif current_root_type == "Expense":
						account_type = "Expense Account"  # Default for Expense accounts
					# For other root_types (Asset, Liability, Equity), account_type can be None
					# Group accounts don't need account_type

				account = frappe.get_doc(
					{
						"doctype": "Account",
						"account_name": child.get("account_name") if from_coa_importer else account_name,
						"company": company,
						"parent_account": parent,
						"is_group": is_group,
						"root_type": current_root_type,
						"report_type": report_type,
						"account_number": account_number,
						"account_type": account_type,
						"account_currency": child.get("account_currency")
						or frappe.get_cached_value("Company", company, "default_currency"),
						"tax_rate": child.get("tax_rate"),
					}
				)

				if root_account or frappe.local.flags.allow_unverified_charts:
					account.flags.ignore_mandatory = True

				account.flags.ignore_permissions = True

				account.insert()

				accounts.append(account_name_in_db)

				_import_accounts(child, account.name, current_root_type)

		# Rebuild NestedSet HSM tree for Account Doctype
		# after all accounts are already inserted.
		frappe.local.flags.ignore_update_nsm = True
		_import_accounts(chart, None, None, root_account=True)
		rebuild_tree("Account")
		frappe.local.flags.ignore_update_nsm = False

