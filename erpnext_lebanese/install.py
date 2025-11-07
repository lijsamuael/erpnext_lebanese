# erpnext_lebanese/install.py
import frappe
import os
import shutil
import json


def after_install():
	"""
	Copy Lebanese chart of accounts JSON to ERPNext's unverified folder
	This allows ERPNext to automatically discover and use it
	"""
	try:
		# Get paths
		lebanese_app_path = frappe.get_app_path("erpnext_lebanese")
		source_file = os.path.join(
			lebanese_app_path,
			"erpnext_lebanese",
			"data",
			"chart_of_accounts",
			"lebanese_standard.json"
		)
		
		erpnext_app_path = frappe.get_app_path("erpnext")
		target_dir = os.path.join(
			erpnext_app_path,
			"erpnext",
			"accounts",
			"doctype",
			"account",
			"chart_of_accounts",
			"unverified"
		)
		
		# Ensure target directory exists
		if not os.path.exists(target_dir):
			os.makedirs(target_dir)
		
		# Target file name - use lb prefix for Lebanon country code
		target_file = os.path.join(target_dir, "lb_lebanese_standard.json")
		
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
		with open(target_file, 'w') as f:
			json.dump(chart_data, f, indent=4, ensure_ascii=False)
		
	except Exception as e:
		# Don't fail installation if this fails
		pass

