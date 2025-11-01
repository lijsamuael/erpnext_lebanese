import frappe

def get_company_types():
    """Get Lebanese company types"""
    return [
        "Holding & Off-Shore",
        "S.A.L Corporat'n", 
        "S.A.R.L Share Part.",
        "Collective Partnerships",
        "Individuel Proprietor"
    ]