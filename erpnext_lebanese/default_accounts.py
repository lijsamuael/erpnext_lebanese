import frappe

BS_ROOTS = {"Asset", "Liability", "Equity"}

ACCOUNT_BLUEPRINTS = {
	"default_bank_account": {"account_number": "5121", "account_type": "Bank"},
	"default_cash_account": {"account_number": "5300", "account_type": "Cash"},
	"default_receivable_account": {
		"account_number": "4111",
		"account_type": "Receivable",
		"root_type": "Asset",
		"report_type": "Balance Sheet",
	},
	"default_payable_account": {
		"account_number": "4011",
		"account_type": "Payable",
		"root_type": "Liability",
		"report_type": "Balance Sheet",
	},
	"default_expense_account": {
		"account_number": "6011",
		"account_type": "Cost of Goods Sold",
		"report_type": "Profit and Loss",
	},
	"default_income_account": {
		"account_number": "7010",
		"account_type": "Income Account",
		"report_type": "Profit and Loss",
	},
	"default_discount_account": {
		"account_number": "4119",
		"account_type": "Receivable",
		"root_type": "Asset",
		"report_type": "Balance Sheet",
	},
	"default_deferred_revenue_account": {"account_number": "4730"},
	"default_deferred_expense_account": {"account_number": "4720"},
	"default_inventory_account": {"account_number": "3100", "account_type": "Stock"},
	"default_provisional_account": {"account_number": "4740"},
	"default_operating_cost_account": {"account_number": "6263.9", "account_type": "Expense Account"},
	"default_advance_received_account": {"account_number": "4191", "account_type": "Receivable"},
	"default_advance_paid_account": {"account_number": "4091", "account_type": "Payable"},
	"purchase_expense_account": {
		"account_number": "6011",
		"account_type": "Cost of Goods Sold",
		"report_type": "Profit and Loss",
	},
	"purchase_expense_contra_account": {"account_number": "6019", "account_type": "Expense Account"},
	"service_expense_account": {"account_number": "6261.5", "account_type": "Expense Account"},
	"stock_adjustment_account": {
		"account_number": "6052",
		"account_type": "Stock Adjustment",
		"root_type": "Expense",
		"report_type": "Profit and Loss",
	},
	"stock_received_but_not_billed_account": {
		"account_number": "3300",
		"account_type": "Stock Received But Not Billed",
		"root_type": "Liability",
		"report_type": "Balance Sheet",
	},
	"write_off_account": {"account_number": "6851.5", "account_type": "Expense Account"},
	"exchange_gain_loss_account": {
		"account_number": "6751",
		"account_type": "Expense Account",
		"root_type": "Expense",
		"report_type": "Profit and Loss",
	},
	"unrealized_exchange_gain_loss_account": {"account_number": "4760"},
	"unrealized_profit_loss_account": {"account_number": "4750"},
	"accumulated_depreciation_account": {
		"account_number": "2823",
		"account_type": "Accumulated Depreciation",
	},
	"depreciation_expense_account": {"account_number": "6512.4", "account_type": "Depreciation"},
	"disposal_account": {"account_number": "7819", "report_type": "Profit and Loss"},
	"capital_work_in_progress_account": {
		"account_number": "2274",
		"account_type": "Capital Work in Progress",
	},
}

WAREHOUSE_BLUEPRINTS = {
	"default_wip_warehouse": {"warehouse_name": "Work In Progress"},
	"default_fg_warehouse": {"warehouse_name": "Finished Goods"},
	"default_in_transit_warehouse": {"warehouse_name": "Goods In Transit", "warehouse_type": "Transit"},
	"default_scrap_warehouse": {"warehouse_name": "Scrap", "warehouse_type": "Scrap"},
}

LOGGER = frappe.logger("erpnext_lebanese.default_accounts")


def build_default_account_map(company: str) -> dict[str, str]:
	cache: dict[str, str] = {}
	defaults: dict[str, str] = {}

	for fieldname, blueprint in ACCOUNT_BLUEPRINTS.items():
		account_name = _ensure_account(company, blueprint, cache)
		if account_name:
			defaults[fieldname] = account_name

	return defaults


def _ensure_account(company: str, blueprint: dict, cache: dict[str, str]) -> str | None:
	account_number = blueprint.get("account_number")
	account_name = None

	if account_number:
		account_name = cache.get(account_number)
		if not account_name:
			account_name = frappe.db.get_value(
				"Account", {"company": company, "account_number": account_number}, "name"
			)
			if account_name:
				cache[account_number] = account_name

	if not account_name and blueprint.get("account_name"):
		account_name = frappe.db.get_value(
			"Account", {"company": company, "account_name": blueprint["account_name"]}, "name"
		)

	if not account_name and blueprint.get("create_if_missing"):
		account_name = _create_account(company, blueprint)
		if account_name and account_number:
			cache[account_number] = account_name

	if account_name:
		updates = {}

		if blueprint.get("account_type"):
			current_type = frappe.db.get_value("Account", account_name, "account_type")
			if current_type != blueprint["account_type"]:
				updates["account_type"] = blueprint["account_type"]

		desired_root = blueprint.get("root_type")
		if desired_root:
			current_root = frappe.db.get_value("Account", account_name, "root_type")
			if current_root != desired_root:
				updates["root_type"] = desired_root

		desired_report = blueprint.get("report_type")
		if not desired_report and desired_root:
			desired_report = "Balance Sheet" if desired_root in BS_ROOTS else "Profit and Loss"
		if desired_report:
			current_report = frappe.db.get_value("Account", account_name, "report_type")
			if current_report != desired_report:
				updates["report_type"] = desired_report

		if updates:
			frappe.db.set_value("Account", account_name, updates)

	return account_name


def _create_account(company: str, blueprint: dict) -> str | None:
	parent_number = blueprint.get("parent_account_number")
	if not parent_number:
		LOGGER.warning("Cannot create account %(number)s without parent in blueprint.", blueprint)
		return None

	parent_account = frappe.db.get_value(
		"Account", {"company": company, "account_number": parent_number}, "name"
	)
	if not parent_account:
		LOGGER.warning(
			"Parent %(parent)s not found while creating %(number)s for %(company)s",
			{
				"parent": parent_number,
				"number": blueprint.get("account_number"),
				"company": company,
			},
		)
		return None

	root_type = blueprint.get("root_type") or frappe.db.get_value(
		"Account", parent_account, "root_type"
	)
	report_type = blueprint.get("report_type")
	if not report_type:
		report_type = "Balance Sheet" if root_type in BS_ROOTS else "Profit and Loss"

	account_doc = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": blueprint.get("account_name") or blueprint.get("account_number"),
			"account_number": blueprint.get("account_number"),
			"company": company,
			"parent_account": parent_account,
			"is_group": 0,
			"root_type": root_type,
			"report_type": report_type,
			"account_type": blueprint.get("account_type"),
			"account_currency": frappe.get_cached_value("Company", company, "default_currency"),
		}
	)
	account_doc.flags.ignore_permissions = True
	account_doc.insert()
	return account_doc.name


def build_company_structural_defaults(company: str) -> dict[str, str]:
	defaults: dict[str, str] = {}

	# Ensure cost center exists first, then get it
	_ensure_cost_center_tree(company)
	primary_cost_center = _get_primary_cost_center(company)
	if primary_cost_center:
		defaults["cost_center"] = primary_cost_center
		defaults["round_off_cost_center"] = primary_cost_center
		defaults["depreciation_cost_center"] = primary_cost_center

	for fieldname, blueprint in WAREHOUSE_BLUEPRINTS.items():
		wh_name = _ensure_warehouse(company, **blueprint)
		if wh_name:
			defaults[fieldname] = wh_name

	return defaults


def _get_primary_cost_center(company: str) -> str | None:
	# First try to find "Main - FE" specifically
	cost_center = frappe.db.get_value(
		"Cost Center",
		{"company": company, "name": "Main - FE", "is_group": 0},
		"name",
	)
	if cost_center:
		return cost_center
	
	# Try with company abbreviation pattern "Main - {abbr}"
	abbr = frappe.db.get_value("Company", company, "abbr")
	if abbr:
		cost_center_name = f"Main - {abbr}"
		cost_center = frappe.db.get_value(
			"Cost Center",
			{"company": company, "name": cost_center_name, "is_group": 0},
			"name",
		)
		if cost_center:
			return cost_center
	
	# Fallback to any "Main" cost center
	cost_center = frappe.db.get_value(
		"Cost Center",
		{"company": company, "cost_center_name": "Main", "is_group": 0},
		"name",
	)
	if cost_center:
		return cost_center
	cost_center = frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name")
	if cost_center:
		return cost_center

	# Ensure cost center tree exists - this will create "Main - {abbr}"
	return _ensure_cost_center_tree(company)


def _ensure_cost_center_tree(company: str) -> str | None:
	abbr = frappe.db.get_value("Company", company, "abbr")
	if not abbr:
		return None

	root_name = f"{company} - {abbr}"
	if not frappe.db.exists("Cost Center", root_name):
		root_doc = frappe.get_doc(
			{
				"doctype": "Cost Center",
				"cost_center_name": company,
				"company": company,
				"is_group": 1,
			}
		)
		root_doc.flags.ignore_permissions = True
		root_doc.flags.ignore_mandatory = True
		root_doc.insert()

	main_name = f"Main - {abbr}"
	if not frappe.db.exists("Cost Center", main_name):
		main_doc = frappe.get_doc(
			{
				"doctype": "Cost Center",
				"cost_center_name": "Main",
				"company": company,
				"is_group": 0,
				"parent_cost_center": root_name,
			}
		)
		main_doc.flags.ignore_permissions = True
		main_doc.insert()
		# Return the name that was just created
		return main_doc.name

	# Return existing cost center name
	return main_name


def _ensure_warehouse(company: str, warehouse_name: str, warehouse_type: str | None = None) -> str | None:
	existing = frappe.db.get_value(
		"Warehouse",
		{"company": company, "warehouse_name": warehouse_name},
		"name",
	)
	if existing:
		return existing

	parent = frappe.db.get_value(
		"Warehouse",
		{"company": company, "warehouse_name": "All Warehouses"},
		"name",
	) or frappe.db.get_value("Warehouse", {"company": company, "is_group": 1}, "name")

	if not parent:
		parent = _ensure_root_warehouse(company)

	if warehouse_type:
		_ensure_warehouse_type(warehouse_type)

	warehouse_doc = frappe.get_doc(
		{
			"doctype": "Warehouse",
			"warehouse_name": warehouse_name,
			"is_group": 0,
			"company": company,
			"parent_warehouse": parent,
			"warehouse_type": warehouse_type,
		}
	)
	warehouse_doc.flags.ignore_permissions = True
	warehouse_doc.flags.ignore_mandatory = True
	warehouse_doc.insert()
	return warehouse_doc.name


def _ensure_warehouse_type(name: str) -> None:
	if frappe.db.exists("Warehouse Type", name):
		return

	doc = frappe.get_doc({"doctype": "Warehouse Type", "warehouse_type": name})
	doc.flags.ignore_permissions = True
	doc.name = name
	doc.insert()


def _ensure_root_warehouse(company: str) -> str:
	root = frappe.db.get_value(
		"Warehouse",
		{"company": company, "warehouse_name": "All Warehouses"},
		"name",
	)
	if root:
		return root

	doc = frappe.get_doc(
		{
			"doctype": "Warehouse",
			"warehouse_name": "All Warehouses",
			"is_group": 1,
			"company": company,
		}
	)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_mandatory = True
	doc.insert()
	return doc.name

