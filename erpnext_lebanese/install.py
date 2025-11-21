# erpnext_lebanese/install.py
import frappe
import os
import json


def _get_chart_paths():
	lebanese_app_path = frappe.get_app_path("erpnext_lebanese")
	source_file = os.path.join(
		lebanese_app_path,
		"data",
		"chart_of_accounts",
		"lebanese_standard.json"
	)

	erpnext_app_path = frappe.get_app_path("erpnext")
	target_dir = os.path.join(
		erpnext_app_path,
		"accounts",
		"doctype",
		"account",
		"chart_of_accounts",
		"unverified"
	)

	target_file = os.path.join(target_dir, "lb_lebanese_standard.json")

	return source_file, target_dir, target_file


def after_install():
	"""
	Copy Lebanese chart of accounts JSON to ERPNext's unverified folder
	This allows ERPNext to automatically discover and use it
	"""
	try:
		source_file, target_dir, target_file = _get_chart_paths()

		# Ensure target directory exists
		if not os.path.exists(target_dir):
			os.makedirs(target_dir)
		
		# Read and validate the source JSON
		with open(source_file, 'r') as f:
			chart_data = json.load(f)
		
		# Ensure it has the required fields
		if not chart_data.get("name"):
			chart_data["name"] = "Lebanese Standard Chart of Accounts"
		if not chart_data.get("country_code"):
			chart_data["country_code"] = "lb"
		if chart_data.get("disabled") is None:
			chart_data["disabled"] = "No"
		
		# Write to target location
		with open(target_file, 'w', encoding='utf-8') as f:
			json.dump(chart_data, f, indent=4, ensure_ascii=False)
		
	except Exception as e:
		# Don't fail installation if this fails
		pass


def after_uninstall():
	"""
	Remove Lebanese chart JSON from ERPNext when the app is uninstalled
	"""
	try:
		_, _, target_file = _get_chart_paths()
		if os.path.exists(target_file):
			os.remove(target_file)
	except Exception:
		# Avoid uninstall failure
		pass

