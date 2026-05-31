import pandas as pd
import json
import os
import numpy as np

class DataCleaner:
    def plan(self, csv_path: str, analysis_kit_json: str) -> dict:
        
        # Load analysis kit
        analysis_kit = json.loads(analysis_kit_json)
        
        # Extract (prefer structured keys, fallback to recommendations text)
        recommendations = analysis_kit.get('cleaning_recommendations', [])
        data_audit = analysis_kit.get('data_audit', {}) or {}
        constant_cols_struct = data_audit.get('constant_cols', []) or []
        high_card_cols_struct = data_audit.get('high_cardinality_cols', []) or []
        leakage_candidates_struct = data_audit.get('leakage_candidates', []) or []
        
        # Initialize cleaning plan
        cleaning_plan = {
            "steps": [],
            "justifications": [],
            # keep explicit lists so apply() doesn't have to parse strings
            "columns_to_remove": list(constant_cols_struct),
            "high_cardinality_cols": list(high_card_cols_struct),
            "leakage_candidates": list(leakage_candidates_struct),
        }


        # Helper to parse list-like text inside a recommendation (e.g. "['a','b']")
        def _parse_list_from_text(text: str):
            try:
                # try json first (if it's valid JSON list)
                return json.loads(text)
            except Exception:
                pass
            t = text.strip().strip("[]")
            if not t:
                return []
            return [x.strip().strip("'").strip('"') for x in t.split(",")]
        
        # Populate cleaning plan based on recommendations
        if 'Address missing values.' in recommendations:
            cleaning_plan["steps"].append("Impute missing values")
            cleaning_plan["justifications"].append("To maintain data integrity and usability.")
        
        if 'Remove duplicate rows.' in recommendations:
            cleaning_plan["steps"].append("Remove duplicates")
            cleaning_plan["justifications"].append("To ensure each record is unique and valid.")
        
        # Prefer structured constant cols; else fallback to parsing recommendation text
        if cleaning_plan["columns_to_remove"] or any("Consider removing constant columns" in rec for rec in recommendations):
            if not cleaning_plan["columns_to_remove"]:
                txt_parts = [rec.split(": ", 1)[1] for rec in recommendations if "Consider removing constant columns" in rec and ": " in rec]
                parsed = []
                for t in txt_parts:
                    parsed += _parse_list_from_text(t)
                cleaning_plan["columns_to_remove"] = list(dict.fromkeys(parsed))
            cleaning_plan["steps"].append("Remove constant columns: {}".format(", ".join(cleaning_plan["columns_to_remove"])))
            cleaning_plan["justifications"].append("To reduce redundancy and improve model performance.")
        
        # High-cardinality note (structured list or parsed text)
        if cleaning_plan["high_cardinality_cols"] or any("Review high cardinality columns" in rec for rec in recommendations):
            if not cleaning_plan["high_cardinality_cols"]:
                txt_parts = [rec.split(": ", 1)[1] for rec in recommendations if "Review high cardinality columns" in rec and ": " in rec]
                parsed = []
                for t in txt_parts:
                    parsed += _parse_list_from_text(t)
                cleaning_plan["high_cardinality_cols"] = list(dict.fromkeys(parsed))
            cleaning_plan["steps"].append("Consider handling high cardinality columns: {}".format(", ".join(cleaning_plan["high_cardinality_cols"])))
            cleaning_plan["justifications"].append("To prevent overfitting and improve interpretability.")
        
        if 'Imbalanced classes detected in target. Consider resampling or generating synthetic data.' in recommendations:
            cleaning_plan["steps"].append("Resample or synthesize data")
            cleaning_plan["justifications"].append("To address class imbalance and improve model training.")
        
       # Leakage candidates (structured list or parsed text)
        if cleaning_plan["leakage_candidates"] or any("Evaluate potential leakage candidates" in rec for rec in recommendations):
            if not cleaning_plan["leakage_candidates"]:
                txt_parts = [rec.split(": ", 1)[1] for rec in recommendations if "Evaluate potential leakage candidates" in rec and ": " in rec]
                parsed = []
                for t in txt_parts:
                    parsed += _parse_list_from_text(t)
                cleaning_plan["leakage_candidates"] = list(dict.fromkeys(parsed))
            cleaning_plan["steps"].append("Evaluate leakage candidates: {}".format(", ".join(cleaning_plan["leakage_candidates"])))
            cleaning_plan["justifications"].append("To prevent data leakage in future model scoring.")
        
        return cleaning_plan

    def apply(self, csv_path: str, plan: dict) -> str:
        
        # Read the CSV (keep a copy for "before" stats)
        df_before = pd.read_csv(csv_path)
        df = df_before.copy()
        
        # Apply each step in the cleaning plan
        for step in plan["steps"]:
            if step == "Impute missing values":
                # --- numeric -> column medians (broadcast ohne chained assignment) ---
                num_cols = df.select_dtypes(include=[np.number]).columns
                if len(num_cols) > 0:
                    med_series = df[num_cols].median(numeric_only=True)  # NaN wenn Spalte komplett leer
                    df[num_cols] = df[num_cols].fillna(med_series)

                # --- categorical -> column modes (pro Spalte zurückschreiben) ---
                cat_cols = df.select_dtypes(include=["object", "category"]).columns
                for c in cat_cols:
                    m = df[c].mode(dropna=True)
                    if not m.empty:
                        df[c] = df[c].fillna(m.iloc[0])

                # --- boolean -> mode (fallback False) ---
                bool_cols = df.select_dtypes(include=["bool"]).columns
                for c in bool_cols:
                    m = df[c].mode(dropna=True)
                    fillv = bool(m.iloc[0]) if not m.empty else False
                    df[c] = df[c].fillna(fillv)
                
            elif step == "Remove duplicates":
                df.drop_duplicates(inplace=True)
            elif step.startswith("Remove constant columns"):
                columns_to_remove = plan.get("columns_to_remove")
                if not columns_to_remove:
                    columns_to_remove = [c.strip() for c in step.split(": ", 1)[1].split(",")]
                df.drop(columns=columns_to_remove, inplace=True, errors='ignore')
            elif step.startswith("Consider handling high cardinality columns"):
                # Placeholder for actual handling logic
                pass
            elif step == "Resample or synthesize data":
                # Placeholder for actual resampling/synthesis logic
                pass
            elif step.startswith("Evaluate leakage candidates"):
                # Placeholder for actual leakage evaluation logic
                pass
        
        # Save cleaned data
        os.makedirs('outputs', exist_ok=True)
        cleaned_csv_path = 'outputs/cleaned_data.csv'
        df.to_csv(cleaned_csv_path, index=False)
        
        # Save before and after stats
        before_and_after_stats = {
            "before": {
                "num_rows": int(len(df_before)),
                "num_columns": int(df_before.shape[1])
            },
            "after": {
                "num_rows": int(len(df)),
                "num_columns": int(df.shape[1])
            }
        }
        with open('outputs/cleaned_data_ref.json', 'w', encoding='utf-8') as json_file:
            json.dump(before_and_after_stats, json_file, indent=2)
        
        return cleaned_csv_path