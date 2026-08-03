import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

import gradio as gr
import pandas as pd

# --- ensure folders exist ---
Path("outputs").mkdir(exist_ok=True)
Path("outputs/plots").mkdir(parents=True, exist_ok=True)

# --- imports of your generated modules ---
import analysis                  # expects run_analysis(...)
from cleaning import DataCleaner # expects class with plan(...), apply(...)
from viz import VizToolKit       # expects class with visualization(...)


# ---------- helpers ----------
def _safe_head_markdown(csv_path: str, n: int = 8) -> str:
    try:
        df = pd.read_csv(csv_path)
        return df.head(n).to_markdown(index=False)
    except Exception as e:
        return f"Preview failed: {e}"

def _safe_head_df(csv_path: str, n: int = 8) -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_path)
        return df.head(n)
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def _collect_pngs_from_dict(d: Dict[str, Any]) -> list:
    out = []
    for v in d.values():
        if isinstance(v, str) and v.lower().endswith(".png") and os.path.exists(v):
            out.append(v)
    return out

def _call_run_analysis(csv_path: str, task_type: str, target: Optional[str], imbalance_threshold: float) -> Dict:
    """
    Be robust to small signature differences:
    1) (csv_file, task_type, target=None, imbalance_threshold=0.2)
    2) (csv_file, task_type, target=None)    # fallback
    """
    try:
        return analysis.run_analysis(csv_path, task_type, target if target else None, float(imbalance_threshold))
    except TypeError:
        return analysis.run_analysis(csv_path, task_type, target if target else None)


# ---------- callbacks ----------
def cb_analyze(file_obj, task_type, target, imbalance_threshold):
    if file_obj is None:
        return None, "Please upload a CSV first.", None

    csv_path = file_obj.name
    res = _call_run_analysis(csv_path, task_type, target, imbalance_threshold)

    # optional mirror for reference
    _write_json("outputs/dataset_audit.json", res)

    rows = res.get("dataset_header", {}).get("num_rows")
    msg = f"Analysis done ✓  (rows={rows})"
    return res, msg, csv_path, res

def cb_plan(csv_path, analysis_dict):
    if not csv_path:
        return None, "No CSV path from analysis."
    if not analysis_dict:
        return None, "No analysis dict. Run Analysis first."

    import json as _json
    payload = _json.dumps(analysis_dict) if isinstance(analysis_dict, dict) else str(analysis_dict)

    cleaner = DataCleaner()
    try:
        plan = cleaner.plan(csv_path, payload)
        msg = "Plan created ✓"
    except Exception as e:
        plan = {"steps": ["Remove duplicates", "Impute missing values"], "columns_to_remove": []}
        msg = f"Plan fallback used (error in plan(): {e})"


    _write_json("outputs/cleaning_plan.json", plan)
    return plan, msg


def cb_apply(csv_path, plan_dict):
    if not csv_path:
        return None, "No CSV path from analysis.", None

    # accept dict or JSON-string; else try file fallback
    import json as _json, os
    if isinstance(plan_dict, str):
        try:
            plan_dict = _json.loads(plan_dict)
        except Exception:
            plan_dict = {}

    if not plan_dict:
        try:
            with open("outputs/cleaning_plan.json", "r", encoding="utf-8") as f:
                plan_dict = _json.load(f)
        except Exception:
            return None, "No plan available. Create a plan first.", None

    cleaner = DataCleaner()
    cleaned_path = cleaner.apply(csv_path, plan_dict)

    # small reference file
    ref = {"cleaned_csv": cleaned_path}
    _write_json("outputs/cleaned_data_ref.json", ref)

    df_head = _safe_head_df(cleaned_path)
    return cleaned_path, f"Cleaning done ✓  (saved: {cleaned_path})", df_head



def cb_visualize(cleaned_path, task_type, target):
    if not cleaned_path or not os.path.exists(cleaned_path):
        return {}, [], "No cleaned CSV found. Run Apply first."

    vt = VizToolKit()
    try:
        vsum = vt.visualization(cleaned_path, task_type, target if target else None)
    except TypeError:
        # extremely defensive: some versions forget the target arg
        vsum = vt.visualization(cleaned_path, task_type)

    # mirror file (if your viz writes it already, this will just overwrite)
    _write_json("outputs/visual_summary.json", vsum)

    gallery = _collect_pngs_from_dict(vsum)
    return vsum, gallery, f"Visualization done ✓  ({len(gallery)} figure(s))"


# ---------- UI ----------
def build_demo():
    with gr.Blocks(title="Agentic DS — Week 3") as demo:
        # state
        st_csv_path = gr.State(None)
        st_analysis = gr.State(None)
        st_plan = gr.State(None)
        st_cleaned = gr.State(None)
        st_viz = gr.State(None)

        with gr.Tab("Overview"):
            csv = gr.File(label="Upload CSV", file_types=[".csv"])
            task_type = gr.Dropdown(choices=["supervised", "unsupervised", "not_sure"], value="not_sure", label="Task Type")
            target = gr.Textbox(label="Target (optional)")
            imb = gr.Slider(0.05, 0.5, step=0.05, value=0.2, label="Imbalance threshold")

            with gr.Row():
                btn_an = gr.Button("Run Analysis", variant="primary")
                btn_an_stop = gr.Button("Stop", variant="stop")  

            msg_an = gr.Markdown()
            out_an = gr.JSON(label="Analysis dict")

            evt_an = btn_an.click(cb_analyze, inputs=[csv, task_type, target, imb], outputs=[out_an, msg_an, st_csv_path, st_analysis])
            
            btn_an_stop.click(None, inputs=None, outputs=None, cancels=[evt_an])

        with gr.Tab("Audit & Clean"):
            btn_plan = gr.Button("Build Plan")
            msg_plan = gr.Markdown()
            out_plan = gr.JSON(label="Cleaning Plan")

            btn_apply = gr.Button("Apply Cleaning", variant="primary")
            msg_apply = gr.Markdown()
            cleaned_path_tb = gr.Textbox(label="Cleaned CSV path", interactive=False)
            preview_df = gr.Dataframe(label="Preview (first rows)", interactive=False)


            btn_plan.click(cb_plan, inputs=[st_csv_path, st_analysis], outputs=[out_plan, msg_plan])
            btn_plan.click(lambda d: d, inputs=[out_plan], outputs=[st_plan])

            btn_apply.click(cb_apply, inputs=[st_csv_path, st_plan], outputs=[st_cleaned, msg_apply, preview_df])
            btn_apply.click(lambda p: p, inputs=[st_cleaned], outputs=[cleaned_path_tb])

        with gr.Tab("Visuals"):
            btn_v = gr.Button("Generate Plots")
            msg_v = gr.Markdown()
            out_vsum = gr.JSON(label="Visual Summary (paths)")
            gallery = gr.Gallery(label="Figures", height=480)

            btn_v.click(cb_visualize, inputs=[st_cleaned, task_type, target], outputs=[out_vsum, gallery, msg_v])
            btn_v.click(lambda d: d, inputs=[out_vsum], outputs=[st_viz])


    return demo


if __name__ == "__main__":
    demo = build_demo()
    demo.launch()
