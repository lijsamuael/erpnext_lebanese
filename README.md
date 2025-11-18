# ERPNext Lebanese

ERPNext Custom App That Works For Lebanese Accounting System

## Overview

This custom ERPNext app provides Lebanese-specific accounting features, including a standardized Chart of Accounts (CoA) and multilingual support for Arabic, French, and English languages. The app automatically configures Lebanese companies with the appropriate chart of accounts and provides a fully localized experience.

## Summary

- Automatic Lebanese company provisioning with default CoA, currency, and fiscal settings
- Updated setup wizard that focuses on Lebanese companies and avoids redundant steps
- Localized Chart of Accounts with Arabic/French/English labels and RTL-aware UI
- Overrides for company creation to ensure consistency between wizard and manual flows
- Server API + client scripts for runtime language switching inside Chart of Accounts

## Features

### 1. Lebanese Standard Chart of Accounts

- **8 Root Accounts**: Pre-configured with the standard Lebanese accounting structure:
  - 1000 - EQUITY & LONG TERM DEBTS (رأس المال)
  - 2000 - FIXED ASSETS (حسابات الأصول الثابتة)
  - 3000 - INVENTORY AND GOODS IN PROCESS (المخزون وقيد الصنع)
  - 4000 - RECEIVABLES & PAYABLES (حسابات الذمم)
  - 5000 - Transferable Participation Deeds (سندات التوظيف)
  - 6000 - COSTS & EXPENSES (حسابات الأعباء)
  - 7000 - INCOME (حسابات الإيرادات)
  - 8000 - Comptes des Engagements Hors Bilan (حسابات الإلتزامات خارج الميزانية)

- **Automatic Installation**: The Lebanese chart is automatically installed when creating a Lebanese company through:
  - Setup Wizard (during initial ERPNext setup)
  - Manual Company Creation (after installation)

### 2. Multilingual Support

- **Three Languages**: Full support for Arabic, French, and English
- **Dynamic Language Switching**: Language selector in Chart of Accounts tree view
- **Account Names**: All account names are stored with translations in the JSON chart file
- **Language Detection**: Automatically detects user's preferred language from system settings

### 3. Right-to-Left (RTL) Support

- **Full RTL Layout**: When Arabic is selected, the entire Chart of Accounts tree view switches to RTL mode
- **Right-Aligned Text**: All account names and text are right-aligned
- **Reversed Layout**: Icons and balance values appear on the left side (right side in RTL context)
- **Automatic Switching**: Seamlessly switches between LTR and RTL based on selected language

### 4. Company Creation Override

- **Automatic Configuration**: Lebanese companies are automatically configured with:
  - Lebanese Standard Chart of Accounts
  - Unverified charts enabled
  - Default accounts set (Receivable and Payable)
- **Validation**: Automatically sets chart of accounts if not specified for Lebanese companies

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/lijsamuael/erpnext_lebanese
bench --site site-name install-app erpnext_lebanese
```

After installation, restart your bench:

```bash
bench restart
bench clear-cache
```

## Usage

### Creating a Lebanese Company

#### During Setup Wizard

1. During ERPNext setup, select "Lebanon" as the country
2. The Lebanese Standard Chart of Accounts will be automatically selected
3. Complete the setup wizard
4. Accounts will be created automatically with multilingual support

#### Manual Company Creation

1. Navigate to **Company** list
2. Click **New**
3. Set **Country** to "Lebanon"
4. The **Chart of Accounts** field will automatically be set to "Lebanese Standard Chart of Accounts"
5. Save the company
6. Accounts will be created automatically

### Using Multilingual Chart of Accounts

1. Navigate to **Chart of Accounts** (Tree view)
2. Select your Lebanese company from the **Company** filter
3. Use the **Account Language** dropdown to switch between:
   - English
   - Arabic (displays in RTL)
   - French
4. Account names will update dynamically based on selected language

## Technical Details

### File Structure

```
erpnext_lebanese/
├── erpnext_lebanese/
│   ├── api.py                          # API endpoints for language labels
│   ├── hooks.py                        # Frappe hooks configuration
│   ├── data/
│   │   └── chart_of_accounts/
│   │       └── lebanese_standard.json  # Chart of Accounts definition
│   ├── overrides/
│   │   ├── company_override.py         # Company DocType override
│   │   ├── chart_of_accounts_create_override.py  # Chart creation logic
│   │   └── setup_wizard_override.py   # Setup wizard customization
│   └── public/
│       ├── css/
│       │   └── account_tree_rtl.css    # RTL styles
│       └── js/
│           └── account_tree.js         # Language selector & RTL logic
```

### Key Components

#### 1. Chart of Accounts JSON Structure

The `lebanese_standard.json` file contains:
- Account hierarchy with parent-child relationships
- Account numbers
- Multilingual names (English, Arabic, French)
- Root types for proper categorization

Example structure:
```json
{
  "tree": {
    "EQUITY & LONG TERM DEBTS": {
      "root_type": "Equity",
      "account_number": "1000",
      "arabic_name": "رأس المال",
      "french_name": "COMPTES DE CAPITAUX PERMANENTS",
      "CAPITAL": {
        "account_number": "10",
        "arabic_name": "رأس المال",
        "french_name": "CAPITAL"
      }
    }
  }
}
```

#### 2. Company Override (`company_override.py`)

- Extends the standard ERPNext `Company` DocType
- Automatically sets chart of accounts for Lebanese companies
- Handles account creation with multilingual support
- Sets default receivable and payable accounts

#### 3. Chart Creation Override (`chart_of_accounts_create_override.py`)

- Custom chart creation logic that handles multilingual metadata
- Properly identifies metadata keys (`arabic_name`, `french_name`)
- Sets default account types for income/expense accounts
- Handles nested account structures

#### 4. Language API (`api.py`)

- Whitelisted method: `get_account_language_labels`
- Returns localized account labels based on selected language
- Caches chart tree for performance
- Maps account numbers to multilingual labels

#### 5. Client-Side JavaScript (`account_tree.js`)

- Adds language selector to Chart of Accounts tree view
- Fetches and applies localized labels
- Handles RTL/LTR switching
- Updates tree nodes dynamically

#### 6. RTL Styles (`account_tree_rtl.css`)

- CSS rules for RTL layout
- Right-aligned text for Arabic
- Proper padding and margin adjustments
- Balance area positioning for RTL

### Hooks Configuration

The app uses several Frappe hooks:

```python
# Override Company DocType
override_doctype_class = {
    "Company": "erpnext_lebanese.overrides.company_override.LebaneseCompany"
}

# Override setup wizard methods
override_whitelisted_methods = {
    "erpnext.setup.setup_wizard.setup_wizard.get_setup_stages": "...",
    "erpnext.setup.setup_wizard.setup_wizard.setup_complete": "..."
}

# Inject JavaScript for Account tree view
doctype_tree_js = {
    "Account": "public/js/account_tree.js"
}

# Include RTL CSS
app_include_css = "/assets/erpnext_lebanese/css/account_tree_rtl.css"
```

## Configuration

### Enabling Balance Display

To show account balances in the Chart of Accounts:

1. Go to **Accounts Settings**
2. Enable **Show Balance in Chart of Accounts**
3. Balances will appear next to account names

### Language Preferences

The app automatically detects the user's language preference from:
- User's language setting in **My Account**
- System default language

You can manually change the language using the dropdown in the Chart of Accounts view.

## Development

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/erpnext_lebanese
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### Building Assets

After making changes to JavaScript or CSS files:

```bash
bench build --apps erpnext_lebanese
bench clear-cache
bench restart
```

### Testing

1. Create a test company with country "Lebanon"
2. Verify chart of accounts is automatically set
3. Check that accounts are created with proper structure
4. Test language switching in Chart of Accounts view
5. Verify RTL layout when Arabic is selected

## Troubleshooting

### Accounts Not Created

- Check that `frappe.local.flags.allow_unverified_charts` is set to `True`
- Verify the chart JSON file is valid
- Check error logs for any validation errors

### Language Not Switching

- Clear browser cache
- Rebuild assets: `bench build --apps erpnext_lebanese`
- Check browser console for JavaScript errors
- Verify the API endpoint is accessible

### RTL Not Working

- Ensure CSS file is loaded (check browser network tab)
- Verify `dir="rtl"` attribute is set on tree wrapper
- Check that `rtl-tree` class is applied
- Clear browser cache and rebuild assets

## License

MIT

## Author

Samuael Ketema
