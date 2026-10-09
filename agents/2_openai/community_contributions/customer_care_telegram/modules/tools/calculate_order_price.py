import json
from modules.tools.setup_sheets import initialize_google_sheets
from modules.config import Config
from modules.setup_logging import setup_logging
from fuzzywuzzy import fuzz, process

logger = setup_logging()

_, df = initialize_google_sheets(config=Config)

# --- Order Tools ---
def calculate_order_price(product_name: str, quantity: int) -> str:
    try:
        if not isinstance(product_name, str) or not product_name.strip():
            return json.dumps({"error": "Invalid product name"})
        if not isinstance(quantity, int) or quantity <= 0:
            return json.dumps({"error": "Quantity must be a positive integer"})
        if 'Perfume Name' not in df.columns or df.empty:
            return json.dumps({"error": "Product data not available"})
        product_row = df[df['Perfume Name'].str.lower() == product_name.lower()]
        if not product_row.empty:
            product_id = product_row['Product ID'].iloc[0]
            price = product_row['Price (PKR)'].iloc[0]
            total_price = price * quantity
            return json.dumps({
                "Product ID": product_id,
                "Total Price (PKR)": total_price,
                "Corrected Name": product_row['Perfume Name'].iloc[0]
            })
        product_names = df['Perfume Name'].tolist()
        matches = process.extract(product_name, product_names, scorer=fuzz.token_sort_ratio)
        top_matches = [match for match in matches if match[1] >= 80]
        if not top_matches:
            return json.dumps({
                "error": f"Product '{product_name}' not found.",
                "suggestions": product_names
            })
        if len(top_matches) == 1 or top_matches[0][1] >= 90:
            corrected_name = top_matches[0][0]
            product_row = df[df['Perfume Name'] == corrected_name]
            product_id = product_row['Product ID'].iloc[0]
            price = product_row['Price (PKR)'].iloc[0]
            total_price = price * quantity
            return json.dumps({
                "Product ID": product_id,
                "Total Price (PKR)": total_price,
                "Corrected Name": corrected_name
            })
        return json.dumps({
            "error": f"Product '{product_name}' not found. Did you mean one of these?",
            "suggestions": [match[0] for match in top_matches]
        })
    except Exception as e:
        return json.dumps({"error": f"Error calculating price: {str(e)}"})