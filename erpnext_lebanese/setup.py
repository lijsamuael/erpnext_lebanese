import frappe

def after_install():
    """Setup Lebanese localization after app installation"""
    try:
        # Add Lebanon to countries if not exists
        if not frappe.db.exists("Country", "Lebanon"):
            country = frappe.new_doc("Country")
            country.country_name = "Lebanon"
            country.code = "LB"
            country.insert()
            frappe.db.commit()
            print("Lebanon country added successfully")
        
        print("ERPNext Lebanese app installed successfully")
        
    except Exception as e:
        print(f"Error during installation: {str(e)}")