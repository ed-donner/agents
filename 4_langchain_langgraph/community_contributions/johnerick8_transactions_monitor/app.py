import gradio as gr
import json
from monitoring import Monitoring


async def setup():
    transactions_monitor = Monitoring()
    await transactions_monitor.setup()
    return transactions_monitor


REQUIRED_FIELDS = ["user_id", "name", "amount", "currency"]

def validate_transaction(tx):
    if not isinstance(tx, dict):
        return False
    for field in REQUIRED_FIELDS:
        if field not in tx:
            return False
    return True


async def process_message(transactions_monitor, transaction_input_text, success_criteria, history):
    
    history = history + [{"role": "user", "content": transaction_input_text}]

    try:
        transaction = json.loads(transaction_input_text)
    except Exception:
        transaction = transaction_input_text
    
    if not validate_transaction(transaction):
        return history + [{
            "role": "assistant",
            "content": "Question: the input is not a valid transaction object. Provide required fields (user_id, name, amount, currency, etc.)"
        }], transactions_monitor
    
    results = await transactions_monitor.run_superstep(transaction, history)
    return results, transactions_monitor


async def reset():
    new_transactions_monitor = Monitoring()
    await new_transactions_monitor.setup()
    return "", "", None, new_transactions_monitor


with gr.Blocks(title="Transactions Monitor", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Monitoring Transactions and Compliance")
    transactions_monitor = gr.State()

    with gr.Row():
        chatbot = gr.Chatbot(label="Transactions Monitor", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            transaction_input = gr.Textbox(
            show_label=False,
            placeholder='Paste transaction JSON here, e.g. {"user_id": "123", "name": "John Doe", "amount": 500, "currency": "USD"}',
            lines=5,
        )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="(Optional) Success criteria"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [transactions_monitor])
    transaction_input.submit(
        process_message,
        [transactions_monitor, transaction_input, success_criteria, chatbot],
        [chatbot, transactions_monitor]
    )
    success_criteria.submit(
        process_message,
        [transactions_monitor, transaction_input, success_criteria, chatbot],
        [chatbot, transactions_monitor]
    )
    go_button.click(
        process_message,
        [transactions_monitor, transaction_input, success_criteria, chatbot],
        [chatbot, transactions_monitor]
    )
    reset_button.click(reset, [], [transaction_input, success_criteria, chatbot, transactions_monitor])


ui.launch(inbrowser=True)