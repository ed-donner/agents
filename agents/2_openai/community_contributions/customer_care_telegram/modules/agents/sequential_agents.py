from google.adk.agents import Agent
from google.adk.agents.sequential_agent import SequentialAgent

from modules.tools.run_pandas_query_tool import run_query_from_agent
from modules.tools.save_order import save_order_to_sheet
from modules.tools.calculate_order_price import calculate_order_price

# --- Agents ---
def create_agents(df, client) -> tuple[SequentialAgent, Agent, Agent, Agent]:

    # --- Product Schema ---
    PRODUCTS_SCHEMA = """
    Products Table Schema:
    - Product ID: String 
    - Perfume Name: String (Noor Mist, Thuraya Essence, Rihla Oud, Layali, Ameenah Musk, Safa Veil, Hanan Bloom, Taybah Elixir, Rayaheen Aura, Zahrah Veil)
    - Fragrance Notes: String 
    - Type: String 
    - Volume (ml): Integer 
    - Price (PKR): Integer 
    - Stock: Integer 
    - Gender: String (Men, Women, Unisex)
    - Alcohol-Free: String (e.g., Yes, No)
    - Collection: String (e.g., Luxury Oud)
    - Scent Strength: String (e.g., Strong, Medium, Light)
    - Rating: Float (e.g., 3.6)
    """

    query_refiner_agent = Agent(
        name="query_refiner_agent_v1",
        description="Refines user queries to ensure they are clear, concise and can be used to generate a python expression to query a pandas DataFrame.",
        instruction=(
            "You take a user query in plain english and refine it into a clear, concise and unambiguous plain english query that can be used to generate a python expression to query a pandas DataFrame."
            f"See the schema for reference: {PRODUCTS_SCHEMA}"
            "Your generated english query should be clear and use column names from the schema."
            "If the query is empty or ambiguous, respond: 'I am sorry, I am unable to understand your query. Please try to be more specific.'"
        ),
    )


    query_generator_agent = Agent(
        name="query_generator_agent_v1",
        description="Generates a pandas expression to query a pandas DataFrame based on a user query in plain english.",
        instruction=(
            "You take a user query in plain english and generate a pandas expression to query a pandas DataFrame."
            "Our dataframe is called `df`. Generate query accordingly."
            f"See the schema for reference: {PRODUCTS_SCHEMA}"
            "Your generated pandas expression should be clear and use column names from the given product_schema."
        ),
    )

    query_validator_agent = Agent(
        name="query_validator_agent_v1",
        description="Validates the generated pandas expression to ensure it is correct and can be used to query a pandas DataFrame.",
        instruction=(
            "You take a pandas expression and validate it to ensure it is correct and can be used to query a pandas DataFrame."
            "Use the tool `run_query_from_agent` with argument use_head=True to validate the query."
            "You return True if the query is valid and False if it is not."
        ),
        tools=[run_query_from_agent]
    )

    data_formatter_agent = Agent(
        name="data_formatter_v1",
        model="gemini-2.0-flash-exp",
        description="Executes validated Python expressions on the full DataFrame and formats results for further processing.",
        instruction=(
            "You take a pandas expression and execute it on a pandas DataFrame."
            "Use the tool `run_query_from_agent` with argument use_head=False to execute the query."
        ),
        tools=[run_query_from_agent],
    )

    convincing_response_agent = Agent(
        name="convincing_response_v1",
        model="gemini-2.0-flash-exp",
        description="Crafts detailed, persuasive responses for product queries, emphasizing quality and competitive pricing.",
        instruction=(
            "You are a Convincing Response AI for Muallim E-commerce. Your purpose is to take structured JSON data from data_formatter_v1 and craft persuasive, conversational responses as a passionate sales agent. Emphasize the quality, uniqueness, and competitive pricing of the perfumes."
            "Only reflect details from the JSON data. Do not make up any details."
            "DO NOT reply in Markdown."
        ),
    )

    product_query_agent = SequentialAgent(
        name="product_query_agent_v1",
        description="Orchestrates product query processing by sequentially invoking the query refiner, query generator, query validator, data formatter, and convincing response agents.",
        sub_agents=[query_refiner_agent, query_generator_agent, query_validator_agent, data_formatter_agent, convincing_response_agent],
    )

    order_form_agent = Agent(
        name="order_form_agent_v1",
        model="gemini-2.0-flash-exp",
        description="Collects order details including phone number, email address and contact mode, shows total bill for confirmation, and saves orders to Google Sheets.",
        instruction=(
            f"""
            You are an order-taking assistant for Muallim E-commerce. Collect order details, display the total bill for confirmation, and save orders to Google Sheets.

            Available Products:
            {df[['Perfume Name']].to_string(index=False)}

            Order Fields:
            - Customer Name: Full name (non-empty).  
            - Phone Number: At least 10 digits.  
            - Email: A valid email address
            - Contact Mode: WhatsApp or Call (case-insensitive).  
            - Products and Quantities: List like "Oud Al Jannah, 2; Rose Musk, 1" (positive quantities).  
            - Payment Method: Cash on Delivery, Bank Transfer, or Easypaisa (case-insensitive).  
            - City: Non-empty string.

            Steps:  
            1. Check `state.order_details` and `state.bill_confirmed`.  
            2. If no details, prompt: "Please provide: 
            - Full name
            - Phone number
            - Email
            - Contact mode (WhatsApp/Call)
            - Products and quantities (e.g., Oud Al Jannah, 2; Rose Musk, 1)
            - Payment method (Cash on Delivery/Bank Transfer/Easypaisa)
            - City
            3. Parse user response (using regex/splitting) to extract fields.  
            4. Validate fields:  
            - Name/City: Non-empty.  
            - Phone: 10+ digits.  
            - Email: A valid email address with sign `@`
            - Contact Mode: WhatsApp/Call.  
            - Products: Use `calculate_order_price` for Product ID, Total Price (PKR), Corrected Name.  
            - Payment: Allowed options.  
            5. If invalid/missing fields:  
            - Store valid fields in `state.order_details` (e.g., `{{'Customer Name': 'John Doe', Email: 'abcd@gmail.com', 'Products': [{{'name': 'Oud Al Jannah', 'quantity': 2}}], ...}}`).  
            - Re-prompt for issues (e.g., "Invalid product. Did you mean [suggestions]? Provide correct details.").  
            6. If all fields collected and `state.bill_confirmed` is False:  
            - Sum Total Price (PKR) from `calculate_order_price`.  
            - Show bill: "Order summary: [Product]: [Quantity] x [Price/unit] PKR = [Total] PKR\nTotal: [Total Bill] PKR\nCustomer: [Name], Phone: [Number], Contact: [Mode], City: [City]\nReply 'confirm' or correct details."  
            - Store bill in `state.order_details['bill']`.  
            7. If user replies 'confirm' and details complete:  
            - Set `state.bill_confirmed` to True.  
            - For each product, create `order_details` with all fields (Customer Name, Phone Number, Email, Contact Mode, Product ID, Quantity, Payment Method, Total Price (PKR), City, Product Name).  
            - Call `save_order_to_sheet` with `order_details` and order ID with `ORD` prefix and 5 digits.  
            - On error: "Error saving order: [error]. Please retry or provide details again."  
            - On success: "Order for [products] placed. Order ID: [ID]. We have sent you an email with your order details as well. Have a great day!"  
            - Clear `state.order_details` and `state.bill_confirmed` on success.
            8. If user sends 'retry', re-process valid fields or re-show bill.  
            9. If no valid products: "No products processed. Please provide products and quantities."  
            10. Always update `state.order_details` after each response.

            Tone: Friendly, professional, patient. Provide examples if needed (e.g., "John Doe, 3369632584, WhatsApp, Oud Al Jannah, 2, Cash on Delivery, Karachi")."""
        ),
        tools=[calculate_order_price, save_order_to_sheet],
    )

    return product_query_agent, order_form_agent, query_refiner_agent, convincing_response_agent