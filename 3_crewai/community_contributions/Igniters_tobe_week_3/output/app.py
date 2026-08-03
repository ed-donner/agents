import gradio as gr

from output.OrderManagement import create_order, get_order_history
from output.ProductCatalog import get_all_categories, get_products_by_category, list_products, search_products
from output.ShoppingCart import add_item, get_cart_contents, get_cart_total, remove_item, update_item_quantity
from output.UserManagement import authenticate_user, register_user


def category_map():
    return {category["name"]: category["category_id"] for category in get_all_categories()}


def parse_quantity(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1


def register_user_ui(username, email, password, confirm_password):
    if password != confirm_password:
        return {"success": False, "message": "Passwords do not match"}
    success, result = register_user(username, email, password)
    if not success:
        return {"success": False, "message": result}
    return {"success": True, "user_id": result}


def login_user_ui(username, password):
    success, result = authenticate_user(username, password)
    if not success:
        return {"success": False, "message": result}
    return {"success": True, **result}


def browse_products_ui(category_name):
    categories = category_map()
    if category_name and category_name in categories:
        return get_products_by_category(categories[category_name])
    return list_products()


def search_products_ui(query, category_name, min_price, max_price):
    categories = category_map()
    category_id = categories.get(category_name) if category_name else None
    return search_products(query or "", category_id, min_price, max_price)


def add_to_cart_ui(user_id, product_id, quantity):
    success, message = add_item(user_id, product_id, parse_quantity(quantity))
    return {"success": success, "message": message, "cart": get_cart_contents(user_id), "totals": get_cart_total(user_id)}


def view_cart_ui(user_id):
    return {"items": get_cart_contents(user_id), "totals": get_cart_total(user_id)}


def update_cart_ui(user_id, product_id, quantity):
    success, message = update_item_quantity(user_id, product_id, parse_quantity(quantity))
    return {"success": success, "message": message, "cart": get_cart_contents(user_id), "totals": get_cart_total(user_id)}


def remove_from_cart_ui(user_id, product_id):
    success, message = remove_item(user_id, product_id)
    return {"success": success, "message": message, "cart": get_cart_contents(user_id), "totals": get_cart_total(user_id)}


def checkout_ui(user_id, line1, city, state, postal_code, card_number):
    shipping_address = {
        "line1": line1,
        "city": city,
        "state": state,
        "postal_code": postal_code,
    }
    payment_info = {
        "method": "card",
        "card_number": card_number,
    }
    success, result = create_order(user_id, shipping_address, payment_info)
    if not success:
        return {"success": False, "message": result}
    return {"success": True, "order": result}


def view_orders_ui(user_id):
    return get_order_history(user_id)


with gr.Blocks(title="E-Commerce Demo") as app:
    gr.Markdown("# E-Commerce Demo")
    with gr.Tab("Auth"):
        with gr.Row():
            with gr.Column():
                reg_username = gr.Textbox(label="Username")
                reg_email = gr.Textbox(label="Email")
                reg_password = gr.Textbox(label="Password", type="password")
                reg_confirm = gr.Textbox(label="Confirm Password", type="password")
                reg_button = gr.Button("Register")
                reg_result = gr.JSON(label="Registration Result")
            with gr.Column():
                login_username = gr.Textbox(label="Username")
                login_password = gr.Textbox(label="Password", type="password")
                login_button = gr.Button("Login")
                login_result = gr.JSON(label="Login Result")
    with gr.Tab("Catalog"):
        category_choices = [""] + list(category_map())
        browse_category = gr.Dropdown(choices=category_choices, value="", label="Category")
        browse_button = gr.Button("Browse")
        search_query = gr.Textbox(label="Search")
        search_category = gr.Dropdown(choices=category_choices, value="", label="Search Category")
        min_price = gr.Number(label="Min Price", value=None)
        max_price = gr.Number(label="Max Price", value=None)
        search_button = gr.Button("Search")
        products_result = gr.JSON(label="Products")
    with gr.Tab("Cart"):
        cart_user_id = gr.Textbox(label="User ID")
        cart_product_id = gr.Textbox(label="Product ID")
        cart_quantity = gr.Number(label="Quantity", value=1, precision=0)
        add_button = gr.Button("Add To Cart")
        view_cart_button = gr.Button("View Cart")
        update_button = gr.Button("Update Quantity")
        remove_button = gr.Button("Remove Item")
        cart_result = gr.JSON(label="Cart")
    with gr.Tab("Checkout"):
        checkout_user_id = gr.Textbox(label="User ID")
        line1 = gr.Textbox(label="Address")
        city = gr.Textbox(label="City")
        state = gr.Textbox(label="State")
        postal_code = gr.Textbox(label="Postal Code")
        card_number = gr.Textbox(label="Card Number")
        checkout_button = gr.Button("Place Order")
        checkout_result = gr.JSON(label="Checkout Result")
    with gr.Tab("Orders"):
        orders_user_id = gr.Textbox(label="User ID")
        orders_button = gr.Button("View Orders")
        orders_result = gr.JSON(label="Orders")

    reg_button.click(register_user_ui, [reg_username, reg_email, reg_password, reg_confirm], reg_result)
    login_button.click(login_user_ui, [login_username, login_password], login_result)
    browse_button.click(browse_products_ui, [browse_category], products_result)
    search_button.click(search_products_ui, [search_query, search_category, min_price, max_price], products_result)
    add_button.click(add_to_cart_ui, [cart_user_id, cart_product_id, cart_quantity], cart_result)
    view_cart_button.click(view_cart_ui, [cart_user_id], cart_result)
    update_button.click(update_cart_ui, [cart_user_id, cart_product_id, cart_quantity], cart_result)
    remove_button.click(remove_from_cart_ui, [cart_user_id, cart_product_id], cart_result)
    checkout_button.click(checkout_ui, [checkout_user_id, line1, city, state, postal_code, card_number], checkout_result)
    orders_button.click(view_orders_ui, [orders_user_id], orders_result)


if __name__ == "__main__":
    app.launch()
