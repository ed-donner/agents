import os
import json
import math
import datetime as dt
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import pandas as pd
import plotly.express as px

from inventory import InventoryManager

APP_TITLE = "Digital Integrated Farm Inventory System"
DB_PATH = os.environ.get("FARM_INVENTORY_DB", "farm_inventory.db")

manager = InventoryManager(DB_PATH)

GREEN = "#4f8f5b"
LIGHT_GREEN = "#e9f6ea"
GOLD = "#c9a227"
LIGHT_GOLD = "#fff7db"
DARK = "#17331d"
MUTED = "#6b7b6d"

CSS = f"""
:root {{
    --green: {GREEN};
    --light-green: {LIGHT_GREEN};
    --gold: {GOLD};
    --light-gold: {LIGHT_GOLD};
    --dark: {DARK};
    --muted: {MUTED};
}}
.gradio-container {{
    background: linear-gradient(180deg, #f7fbf7 0%, #fdfbf4 100%);
}}
#hero {{
    background: linear-gradient(135deg, rgba(79,143,91,0.15), rgba(201,162,39,0.16));
    border: 1px solid rgba(79,143,91,0.15);
    border-radius: 20px;
    padding: 22px 24px;
}}
.card {{
    background: white;
    border: 1px solid rgba(23,51,29,0.08);
    border-radius: 18px;
    box-shadow: 0 6px 24px rgba(23,51,29,0.06);
    padding: 18px;
}}
.small-note {{
    color: var(--muted);
    font-size: 0.92rem;
}}
.section-title {{
    color: var(--dark);
    font-weight: 700;
    margin-bottom: 0.4rem;
}}
.badge {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.82rem;
    margin-right: 6px;
}}
.badge-green {{
    background: #e3f4e6;
    color: #1f6b2b;
}}
.badge-gold {{
    background: #fff0c9;
    color: #8f6a00;
}}
"""

def money(x: Any) -> str:
    try:
        return f"NGN {float(x):,.2f}"
    except Exception:
        return "NGN 0.00"

def safe_date_str(s: Optional[str]) -> str:
    return s if s else ""

def df_from_records(records: List[Dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)

def add_inventory(item_name, unit, unit_cost, supplier, quantity, reorder_threshold):
    if not item_name:
        return "Item name is required.", refresh_all()
    try:
        manager.add_inventory_item(item_name, unit, float(unit_cost), supplier, float(quantity), float(reorder_threshold))
        warn = ""
        if float(quantity) < float(reorder_threshold):
            warn = " Warning: quantity is below reorder threshold."
        return f"Inventory item added successfully.{warn}", refresh_all()
    except Exception as e:
        return f"Error: {e}", refresh_all()

def update_inventory(item_id, delta, tx_type, linked_entity):
    try:
        manager.update_inventory_item(int(item_id), float(delta), tx_type)
        if linked_entity:
            txs = manager.get_transactions()
            if txs:
                pass
        return "Inventory updated and transaction logged.", refresh_all()
    except Exception as e:
        return f"Error: {e}", refresh_all()

def add_crop(planting_date, field_assignment, expected_yield, notes):
    try:
        manager.add_crop(planting_date, field_assignment, float(expected_yield), notes)
        return "Crop added successfully.", refresh_all()
    except Exception as e:
        return f"Error: {e}", refresh_all()

def update_crop(crop_id, harvest_date, growth_stage, health_status, actual_yield, notes):
    try:
        kwargs = {}
        if harvest_date:
            kwargs["harvest_date"] = harvest_date
        if growth_stage:
            kwargs["growth_stage"] = growth_stage
        if health_status:
            kwargs["health_status"] = health_status
        if actual_yield not in [None, ""]:
            kwargs["actual_yield"] = float(actual_yield)
        if notes is not None:
            kwargs["notes"] = notes
        manager.update_crop(int(crop_id), **kwargs)
        return "Crop updated successfully.", refresh_all()
    except Exception as e:
        return f"Error: {e}", refresh_all()

def add_livestock(species, breed, birth_date, weight, field_assignment):
    try:
        manager.register_livestock(species, breed, birth_date, float(weight), field_assignment)
        return "Livestock registered successfully.", refresh_all()
    except Exception as e:
        return f"Error: {e}", refresh_all()

def update_livestock(animal_id, weight, health_status, vaccination_records):
    try:
        kwargs = {}
        if weight not in [None, ""]:
            kwargs["weight"] = float(weight)
        if health_status:
            kwargs["health_status"] = health_status
        if vaccination_records is not None:
            kwargs["vaccination_records"] = vaccination_records
        manager.update_livestock(int(animal_id), **kwargs)
        return "Livestock updated successfully.", refresh_all()
    except Exception as e:
        return f"Error: {e}", refresh_all()

def make_tables() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    crops = df_from_records(manager.get_crops())
    livestock = df_from_records(manager.get_livestock())
    inventory = df_from_records(manager.get_inventory_items())
    tx = df_from_records(manager.get_transactions())

    if not crops.empty:
        for col in ["expected_yield", "actual_yield"]:
            if col in crops.columns:
                crops[col] = crops[col].apply(lambda v: None if pd.isna(v) else float(v))
    if not livestock.empty and "weight" in livestock.columns:
        livestock["weight"] = livestock["weight"].apply(lambda v: None if pd.isna(v) else float(v))
    if not inventory.empty:
        if "unit_cost" in inventory.columns:
            inventory["unit_cost"] = inventory["unit_cost"].apply(lambda v: float(v))
        inventory["reorder_alert"] = inventory["quantity"] < inventory["reorder_threshold"]
    if not tx.empty and "unit_cost" in tx.columns:
        tx["unit_cost"] = tx["unit_cost"].apply(lambda v: float(v))
    return crops, livestock, inventory, tx

def build_chart(inventory_df: pd.DataFrame):
    if inventory_df.empty:
        fig = px.bar(title="Inventory Levels")
        fig.update_layout(template="plotly_white", height=420)
        return fig
    plot_df = inventory_df.copy()
    plot_df["status"] = plot_df.apply(
        lambda r: "Below threshold" if r["quantity"] < r["reorder_threshold"] else "Healthy stock",
        axis=1,
    )
    fig = px.bar(
        plot_df,
        x="item_name",
        y="quantity",
        color="status",
        text="quantity",
        title="Inventory Levels vs Reorder Threshold",
        color_discrete_map={"Below threshold": "#d9534f", "Healthy stock": GREEN},
    )
    fig.add_hline(y=plot_df["reorder_threshold"].mean(), line_dash="dot", line_color=GOLD)
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        height=420,
        xaxis_title="Item",
        yaxis_title="Quantity",
        legend_title_text="Status",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig

def summary_text(crops: pd.DataFrame, livestock: pd.DataFrame, inventory: pd.DataFrame, tx: pd.DataFrame) -> str:
    low_stock = 0 if inventory.empty else int((inventory["quantity"] < inventory["reorder_threshold"]).sum())
    healthy_crops = 0 if crops.empty else int((crops["health_status"] == "healthy").sum())
    diseased_livestock = 0 if livestock.empty else int((livestock["health_status"] == "diseased").sum())
    return (
        f"<span class='badge badge-green'>Crops: {len(crops)}</span>"
        f"<span class='badge badge-gold'>Livestock: {len(livestock)}</span>"
        f"<span class='badge badge-green'>Inventory Items: {len(inventory)}</span>"
        f"<span class='badge badge-gold'>Transactions: {len(tx)}</span>"
        f"<br><br>"
        f"Healthy crops: <b>{healthy_crops}</b> &nbsp;|&nbsp; "
        f"Diseased livestock: <b>{diseased_livestock}</b> &nbsp;|&nbsp; "
        f"Low-stock items: <b>{low_stock}</b>"
    )

def refresh_all():
    crops, livestock, inventory, tx = make_tables()
    chart = build_chart(inventory)
    hero = summary_text(crops, livestock, inventory, tx)
    return (
        crops,
        livestock,
        inventory,
        tx,
        chart,
        hero,
        crops,
        livestock,
        inventory,
        tx,
    )

def filter_df(df: pd.DataFrame, query: str) -> pd.DataFrame:
    if df.empty or not query:
        return df
    q = query.lower().strip()
    mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False)).any(axis=1)
    return df[mask]

def report(start_date, end_date, report_type):
    try:
        s = start_date.isoformat() if hasattr(start_date, "isoformat") else str(start_date)
        e = end_date.isoformat() if hasattr(end_date, "isoformat") else str(end_date)
        rep = manager.generate_report(s, e, report_type)
        df = df_from_records(rep.get("data", []))
        return df, json.dumps(rep, indent=2, default=str)
    except Exception as e:
        return pd.DataFrame(), f"Error: {e}"

with gr.Blocks(theme=gr.themes.Soft(primary_hue="green", secondary_hue="amber"), css=CSS, title=APP_TITLE) as demo:
    gr.Markdown(
        f"""
<div id="hero">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">
    <div>
      <h1 style="margin:0;color:{DARK};">{APP_TITLE}</h1>
      <div class="small-note">Clean prototype dashboard for crops, livestock, inventory, transactions, and reports.</div>
    </div>
    <div style="text-align:right;color:{MUTED};">
      <div><b>SQLite</b> persistence</div>
      <div><b>NGN</b> currency formatting</div>
      <div><b>Auto-seeded</b> demo records on first run</div>
    </div>
  </div>
</div>
"""
    )

    with gr.Row():
        refresh_btn = gr.Button("Refresh Dashboard", variant="primary")
        status = gr.Markdown("", elem_classes=["card"])

    with gr.Tabs():
        with gr.TabItem("Overview"):
            crops_df, livestock_df, inventory_df, tx_df = make_tables()
            chart = build_chart(inventory_df)
            hero_md = gr.HTML(summary_text(crops_df, livestock_df, inventory_df, tx_df))
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Inventory Levels")
                    plot = gr.Plot(value=chart)
                with gr.Column(scale=1):
                    gr.Markdown("### Quick Search")
                    search_input = gr.Textbox(label="Search across tables", placeholder="Type a crop, field, species, item, or transaction text...")
                    search_btn = gr.Button("Search")
                    search_result = gr.Dataframe(label="Matched Rows", interactive=False)
            with gr.Row():
                crops_preview = gr.Dataframe(label="Crops", value=crops_df, interactive=False)
                livestock_preview = gr.Dataframe(label="Livestock", value=livestock_df, interactive=False)
            with gr.Row():
                inventory_preview = gr.Dataframe(label="Inventory", value=inventory_df, interactive=False)
                tx_preview = gr.Dataframe(label="Transactions", value=tx_df, interactive=False)

        with gr.TabItem("Crops"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Add Crop")
                    crop_planting = gr.Textbox(label="Planting Date (YYYY-MM-DD)", value=dt.date.today().isoformat())
                    crop_field = gr.Textbox(label="Field Assignment", value="Field D")
                    crop_expected = gr.Number(label="Expected Yield", value=1500.0)
                    crop_notes = gr.Textbox(label="Notes", lines=3, value="New crop row added from dashboard.")
                    add_crop_btn = gr.Button("Add Crop", variant="primary")
                with gr.Column():
                    gr.Markdown("### Update Crop")
                    crop_id = gr.Number(label="Crop ID", value=1)
                    crop_harvest = gr.Textbox(label="Harvest Date (YYYY-MM-DD)", placeholder="Optional")
                    crop_stage = gr.Dropdown(["Seedling", "Vegetative", "Flowering", "Harvested"], label="Growth Stage", value="Vegetative")
                    crop_health = gr.Dropdown(["healthy", "at-risk", "diseased"], label="Health Status", value="healthy")
                    crop_actual = gr.Number(label="Actual Yield", value=None)
                    crop_update_notes = gr.Textbox(label="Notes", lines=3, value="Updated from UI.")
                    update_crop_btn = gr.Button("Update Crop", variant="primary")
            crop_msg = gr.Markdown()
            crop_table = gr.Dataframe(label="Crops Table", value=crops_df, interactive=False)

        with gr.TabItem("Livestock"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Register Livestock")
                    animal_species = gr.Textbox(label="Species", value="Sheep")
                    animal_breed = gr.Textbox(label="Breed", value="Yankasa")
                    animal_birth = gr.Textbox(label="Date of Birth (YYYY-MM-DD)", value="2023-02-10")
                    animal_weight = gr.Number(label="Weight", value=22.5)
                    animal_field = gr.Textbox(label="Field Assignment", value="Pasture 3")
                    add_livestock_btn = gr.Button("Register Animal", variant="primary")
                with gr.Column():
                    gr.Markdown("### Update Livestock")
                    animal_id = gr.Number(label="Animal ID", value=1)
                    animal_new_weight = gr.Number(label="Weight", value=None)
                    animal_health = gr.Dropdown(["healthy", "at-risk", "diseased"], label="Health Status", value="healthy")
                    animal_vax = gr.Textbox(label="Vaccination Records", lines=3, value="Routine update from dashboard.")
                    update_livestock_btn = gr.Button("Update Livestock", variant="primary")
            livestock_msg = gr.Markdown()
            livestock_table = gr.Dataframe(label="Livestock Table", value=livestock_df, interactive=False)

        with gr.TabItem("Inventory & Transactions"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Add Inventory Item")
                    inv_name = gr.Textbox(label="Item Name", value="Layer Feed")
                    inv_unit = gr.Textbox(label="Unit of Measure", value="bags")
                    inv_cost = gr.Number(label="Unit Cost (NGN)", value=9500.0)
                    inv_supplier = gr.Textbox(label="Supplier", value="FarmSupply Ltd.")
                    inv_qty = gr.Number(label="Quantity on Hand", value=25.0)
                    inv_threshold = gr.Number(label="Reorder Threshold", value=30.0)
                    add_inv_btn = gr.Button("Add Item", variant="primary")
                with gr.Column():
                    gr.Markdown("### Record Inventory Movement")
                    move_item_id = gr.Number(label="Item ID", value=1)
                    move_delta = gr.Number(label="Quantity Delta (+ purchase, - use/disposal)", value=-5.0)
                    move_type = gr.Dropdown(["purchase", "use", "disposal"], label="Transaction Type", value="use")
                    move_linked = gr.Textbox(label="Linked Entity", value="Field A / Maize block")
                    move_btn = gr.Button("Apply Movement", variant="primary")
            inv_msg = gr.Markdown()
            inventory_table = gr.Dataframe(label="Inventory Table", value=inventory_df, interactive=False)
            tx_table = gr.Dataframe(label="Transactions Table", value=tx_df, interactive=False)

        with gr.TabItem("Reports"):
            with gr.Row():
                report_start = gr.Textbox(label="Start Date", value=dt.date.today() - dt.timedelta(days=365))
                report_end = gr.Textbox(label="End Date", value=dt.date.today())
                report_type = gr.Dropdown(
                    ["crop performance", "livestock health", "inventory status", "transactions"],
                    value="crop performance",
                    label="Report Type",
                )
            report_btn = gr.Button("Generate Report", variant="primary")
            report_df = gr.Dataframe(label="Report Output", interactive=False)
            report_json = gr.Code(label="Raw Report JSON", language="json")

    def do_search(query):
        crops, livestock, inventory, tx = make_tables()
        merged = pd.concat(
            [
                crops.assign(__source="crops"),
                livestock.assign(__source="livestock"),
                inventory.assign(__source="inventory"),
                tx.assign(__source="transactions"),
            ],
            ignore_index=True,
            sort=False,
        )
        result = filter_df(merged.fillna(""), query)
        return result

    search_btn.click(do_search, inputs=[search_input], outputs=[search_result])
    refresh_btn.click(refresh_all, inputs=None, outputs=[crops_preview, livestock_preview, inventory_preview, tx_preview, plot, hero_md, crop_table, livestock_table, inventory_table, tx_table])

    add_crop_btn.click(add_crop, inputs=[crop_planting, crop_field, crop_expected, crop_notes], outputs=[crop_msg, crop_table, livestock_table, inventory_table, tx_table, plot, hero_md, crops_preview, livestock_preview, inventory_preview, tx_preview])
    update_crop_btn.click(update_crop, inputs=[crop_id, crop_harvest, crop_stage, crop_health, crop_actual, crop_update_notes], outputs=[crop_msg, crop_table, livestock_table, inventory_table, tx_table, plot, hero_md, crops_preview, livestock_preview, inventory_preview, tx_preview])

    add_livestock_btn.click(add_livestock, inputs=[animal_species, animal_breed, animal_birth, animal_weight, animal_field], outputs=[livestock_msg, crop_table, livestock_table, inventory_table, tx_table, plot, hero_md, crops_preview, livestock_preview, inventory_preview, tx_preview])
    update_livestock_btn.click(update_livestock, inputs=[animal_id, animal_new_weight, animal_health, animal_vax], outputs=[livestock_msg, crop_table, livestock_table, inventory_table, tx_table, plot, hero_md, crops_preview, livestock_preview, inventory_preview, tx_preview])

    add_inv_btn.click(add_inventory, inputs=[inv_name, inv_unit, inv_cost, inv_supplier, inv_qty, inv_threshold], outputs=[inv_msg, crop_table, livestock_table, inventory_table, tx_table, plot, hero_md, crops_preview, livestock_preview, inventory_preview, tx_preview])
    move_btn.click(update_inventory, inputs=[move_item_id, move_delta, move_type, move_linked], outputs=[inv_msg, crop_table, livestock_table, inventory_table, tx_table, plot, hero_md, crops_preview, livestock_preview, inventory_preview, tx_preview])

    report_btn.click(report, inputs=[report_start, report_end, report_type], outputs=[report_df, report_json])

    demo.load(refresh_all, inputs=None, outputs=[crops_preview, livestock_preview, inventory_preview, tx_preview, plot, hero_md, crop_table, livestock_table, inventory_table, tx_table])

if __name__ == "__main__":
    demo.launch()