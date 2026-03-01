from budget_manager import BudgetTracker
import gradio as gr

tracker = BudgetTracker()

def add_expense(amount, category, date):
    tracker.add_expense(float(amount), category, date)
    return f"Added {amount} for {category} on {date}"

def total_spending():
    return tracker.calculate_total_spending()

def spending_by_category(category):
    return tracker.calculate_spending_by_category(category)

def save_expenses(file_path):
    tracker.save_to_file(file_path)
    return f"Expenses saved to {file_path}"

def load_expenses(file_path):
    tracker.load_from_file(file_path)
    return f"Expenses loaded from {file_path}"

with gr.Blocks() as demo:
    gr.Markdown("### Budget Tracker")
    
    with gr.Tab("Add Expense"):
        amount = gr.Number(label="Amount")
        category = gr.Textbox(label="Category")
        date = gr.Textbox(label="Date (YYYY-MM-DD)")
        add_button = gr.Button("Add Expense")
        add_output = gr.Textbox(label="Output")
        
        add_button.click(add_expense, inputs=[amount, category, date], outputs=add_output)
    
    with gr.Tab("View Total Spending"):
        total_button = gr.Button("Calculate Total Spending")
        total_output = gr.Textbox(label="Total Spending")
        
        total_button.click(total_spending, outputs=total_output)
    
    with gr.Tab("View Spending by Category"):
        category_input = gr.Textbox(label="Category")
        category_button = gr.Button("Calculate Spending by Category")
        category_output = gr.Textbox(label="Spending Amount")
        
        category_button.click(spending_by_category, inputs=category_input, outputs=category_output)
    
    with gr.Tab("File Operations"):
        file_path_input = gr.Textbox(label="File Path")
        save_button = gr.Button("Save Expenses")
        load_button = gr.Button("Load Expenses")
        file_output = gr.Textbox(label="File Operation Output")
        
        save_button.click(save_expenses, inputs=file_path_input, outputs=file_output)
        load_button.click(load_expenses, inputs=file_path_input, outputs=file_output)

demo.launch()