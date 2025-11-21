import frappe
from frappe.query_builder import DocType
from erpnext.accounts.report.financial_statements import sort_accounts


@frappe.whitelist()
def get_children(doctype, parent, company, is_root=False, include_disabled=False):
	"""
	Drop-in replacement for erpnext.accounts.utils.get_children that avoids raw SQL expressions
	in filters (unsupported by the current frappe.qb query engine).
	"""
	if isinstance(include_disabled, str):
		include_disabled = frappe.parse_json(include_disabled)
	if isinstance(is_root, str):
		is_root = frappe.parse_json(is_root)

	parent_fieldname = f"parent_{frappe.scrub(doctype)}"
	doc = DocType(doctype)
	parent_field = getattr(doc, parent_fieldname)

	select_fields = [doc.name.as_("value"), doc.is_group.as_("expandable")]

	# Additional fields required for Account tree view, mirroring upstream behaviour
	if doctype == "Account":
		select_fields.append(doc.root_type)

	query = frappe.qb.from_(doc).select(*select_fields)

	# Apply docstatus filter if column exists (matches upstream behaviour)
	if frappe.db.has_column(doctype, "docstatus"):
		query = query.where(doc.docstatus < 2)

	if frappe.db.has_column(doctype, "disabled") and not include_disabled:
		query = query.where(doc.disabled == 0)

	if is_root:
		# Parent is blank or null for root nodes
		query = query.where((parent_field == "") | parent_field.isnull())

		if doctype == "Account":
			query = query.select(doc.report_type, doc.account_currency)

		if frappe.db.has_column(doctype, "company") and company:
			query = query.where(doc.company == company)
	else:
		query = query.where(parent_field == parent)
		query = query.select(parent_field.as_("parent"))

		if doctype == "Account":
			query = query.select(doc.account_currency)

	records = query.run(as_dict=True)

	if doctype == "Account":
		sort_accounts(records, is_root, key="value")

	return records

