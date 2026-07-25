import json
import pandas as pd
from fuzzywuzzy import fuzz, process
import gspread


from modules.tools.setup_sheets import initialize_google_sheets

from modules.config import Config
client, df = initialize_google_sheets(config=Config)

from modules.setup_logging import setup_logging
logger = setup_logging()

# --- Order Status Check Tool ---
def check_order_status(order_id: str, customer_name: str, phone_number: str) -> str:
    try:
        orders_sheet = client.open("Muallim E-commerce").get_worksheet(1)
        data = orders_sheet.get_all_values()
        orders_df = pd.DataFrame(data[1:], columns=data[0])
    
        if orders_df.empty:
            return json.dumps({"error": "No orders found in the database"})
        
        # Match order based on Order ID, Customer Name, and Phone Number
        matched_order = orders_df[
            (orders_df['Order ID'].str.lower() == order_id.lower()) &
            (orders_df['Customer Name'].str.lower() == customer_name.lower()) &
            (orders_df['Phone Number'].astype(str) == phone_number)
        ]

        if matched_order.empty:
            # Fuzzy match for customer name if exact match fails
            names = orders_df['Customer Name'].tolist()
            name_matches = process.extract(customer_name, names, scorer=fuzz.token_sort_ratio, limit=3)
            suggestions = [match[0] for match in name_matches if match[1] >= 80]
            return json.dumps({
                "error": f"No order found for Order ID '{order_id}', Customer Name '{customer_name}', and Phone Number '{phone_number}'.",
                "suggestions": suggestions if suggestions else ["Please verify your details and try again."]
            })

        order_details = matched_order.iloc[0]
        return json.dumps({
            "success": True,
            "order_id": order_details['Order ID'],
            "tracking_link": order_details['Order Tracking Link'],
            "order_status": order_details['Order Status'],
            "delivery_status": order_details['Delivery Status'],
            "product_id": order_details['Product ID'],
            "quantity": order_details['Quantity'],
            "total_price": order_details['Total Price (PKR)'],
            "order_date": order_details['Order Date'],
            "city": order_details['City']
        })

    except gspread.exceptions.APIError as e:
        logger.error(f"Google Sheets API error: {str(e)}")
        return json.dumps({"error": f"Failed to check order status due to Google Sheets error: {str(e)}"})
    except Exception as e:
        logger.error(f"Error checking order status for {order_id}: {str(e)}")
        return json.dumps({"error": f"Failed to check order status: {str(e)}"})