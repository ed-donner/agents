from typing import Optional, Dict, Any
from modules.setup_logging import setup_logging

logger = setup_logging()

from modules.tools.setup_sheets import initialize_google_sheets

from modules.config import Config
client, df = initialize_google_sheets(config=Config)

import random
import datetime
import gspread

from modules.tools.send_email import send_email

# --- Order Tools ---
def save_order_to_sheet(order_details: Dict[str, Any], order_id: Optional[str] = None) -> str:

    try:
        required_fields = ['Customer Name', 'Phone Number', 'Contact Mode', 'Product ID', 'Quantity', 'Payment Method', 'Total Price (PKR)', 'City', 'Product Name', 'Email']
        missing_fields = [field for field in required_fields if field not in order_details]
        if missing_fields:
            logger.error(f"Missing required fields in order_details: {missing_fields}")
            return f"❌ Sorry, the order could not be placed due to missing information: {', '.join(missing_fields)}. Please try again."
        
        orders_sheet = client.open("Muallim E-commerce").get_worksheet(1)
        if order_id is None:
            order_id = f"ORD{random.randint(100, 999)}"
        today_date = datetime.date.today().isoformat()
        tracking_link = f"https://muallim.shop/track_order{order_id}"
        row = [
            order_id,
            order_details['Customer Name'],
            order_details['Phone Number'],
            order_details['Contact Mode'],
            order_details['Product ID'],
            order_details['Quantity'],
            today_date,
            "Processing",
            order_details['Payment Method'],
            order_details['Total Price (PKR)'],
            order_details['City'],
            tracking_link,
            "Processing"
        ]
        orders_sheet.append_row(row)
        logger.info(f"Order saved successfully: Order ID {order_id}, Product {order_details['Product Name']}")

        email_body = f"""
        Thank you for your order, {order_details['Customer Name']}!

        We’re excited to confirm your order with Muallim E-commerce. Here are the details:

        Order ID: {order_id}
        Product: {order_details['Product Name']}
        Quantity: {order_details['Quantity']}
        Total: {order_details['Total Price (PKR)']} PKR
        Payment Method: {order_details['Payment Method']}
        City: {order_details['City']}

        You can track your order here: {tracking_link}

        We’ll contact you via {order_details['Contact Mode']} at {order_details['Phone Number']} with updates. If you have any questions, feel free to reach out!

        Best regards,
        The Muallim E-commerce Team
        """

        send_email(order_details['Email'], email_body)

        return f"✅ Order for {order_details['Product Name']} placed successfully. Order ID: {order_id}. Track it here: {tracking_link}."
    except gspread.exceptions.APIError as e:
        logger.error(f"Google Sheets API error: {str(e)}")
        return f"❌ Sorry, there was an issue with Google Sheets: {str(e)}. Please try again later."
    except Exception as e:
        logger.error(f"Failed to save order: {str(e)}")
        return f"❌ Sorry, something went wrong while placing the order for {order_details.get('Product Name', 'unknown product')}: {str(e)}. Please try again."
