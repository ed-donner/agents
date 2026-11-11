import gradio as gr

from trading_desk import TradingDesk


desk = TradingDesk()


async def run_cycle():
    result = await desk.run_cycle()
    traders_df, holdings_df, actions_df, reviews_df, alerts_df = desk.snapshot_tables()
    trader_summary = '\n\n'.join([f"### {item['name']}\n{item['summary']}" for item in result['trader_summaries']])
    return (
        result['manager_pre'],
        result['risk_pre'],
        trader_summary,
        result['manager_post'],
        result['risk_post'],
        traders_df,
        holdings_df,
        actions_df,
        reviews_df,
        alerts_df,
    )


def reset_desk():
    desk.reset()
    traders_df, holdings_df, actions_df, reviews_df, alerts_df = desk.snapshot_tables()
    return (
        'Desk reset to starting strategies.',
        '',
        '',
        '',
        '',
        traders_df,
        holdings_df,
        actions_df,
        reviews_df,
        alerts_df,
    )


with gr.Blocks(title='Autonomous Trading Desk', theme=gr.themes.Default(primary_hue='sky')) as ui:
    gr.Markdown('## Autonomous Trading Desk')
    gr.Markdown('Adds a Portfolio Manager and Risk Officer layer above a smaller autonomous trading team.')

    with gr.Row():
        run_button = gr.Button('Run Desk Cycle', variant='primary')
        reset_button = gr.Button('Reset Desk', variant='stop')

    with gr.Row():
        manager_pre = gr.Markdown(label='Portfolio Manager (Pre-Trade)')
        risk_pre = gr.Markdown(label='Risk Officer (Pre-Trade)')

    trader_output = gr.Markdown(label='Trader Actions')

    with gr.Row():
        manager_post = gr.Markdown(label='Portfolio Manager (Post-Trade)')
        risk_post = gr.Markdown(label='Risk Officer (Post-Trade)')

    with gr.Row():
        traders_df = gr.Dataframe(label='Trader Snapshots')
        holdings_df = gr.Dataframe(label='Desk Holdings')

    with gr.Row():
        actions_df = gr.Dataframe(label='Recent Trader Actions')
        reviews_df = gr.Dataframe(label='Desk Reviews')
        alerts_df = gr.Dataframe(label='Risk Alerts')

    run_button.click(
        run_cycle,
        outputs=[manager_pre, risk_pre, trader_output, manager_post, risk_post, traders_df, holdings_df, actions_df, reviews_df, alerts_df],
    )
    reset_button.click(
        reset_desk,
        outputs=[manager_pre, risk_pre, trader_output, manager_post, risk_post, traders_df, holdings_df, actions_df, reviews_df, alerts_df],
    )

ui.launch(inbrowser=True)
