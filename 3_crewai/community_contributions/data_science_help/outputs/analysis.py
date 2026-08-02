import pandas as pd
import numpy as np
import re
import warnings

def run_analysis(csv_file: str, task_type: str, target: str = None, imbalance_threshold: float = 0.2) -> dict:
    # Read CSV into DataFrame
    df = pd.read_csv(csv_file)

    # Infer dtypes and categorize columns
    dtypes = df.dtypes
    dtype_summary = {
        'numeric': df.select_dtypes(include=[np.number]).columns.tolist(),
        'categorical': df.select_dtypes(include=['object', 'category']).columns.tolist(),
        'boolean': df.select_dtypes(include=['bool']).columns.tolist(),
        # robust across pandas versions (handles tz-aware as well)
        'datetime': [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    }

    # Heuristik: sieht eine Series wie Datum/Zeit aus? (Regex auf Stichprobe)
    def _looks_like_datetime_series(s: pd.Series, sample: int = 50) -> bool:
        patterns = [
            r"^\d{4}-\d{2}-\d{2}",      # 2023-09-30
            r"^\d{2}/\d{2}/\d{4}",      # 09/30/2023
            r"^\d{2}\.\d{2}\.\d{4}",    # 30.09.2023
            r"^\d{4}/\d{2}/\d{2}",      # 2023/09/30
            r"^\d{2}-\d{2}-\d{4}",      # 30-09-2023
            r"^\d{2}:\d{2}:\d{2}",      # 12:34:56 (time)
        ]
        rx = re.compile("|".join(patterns))
        vals = s.dropna().astype(str).head(sample)
        if len(vals) == 0:
            return False
        return vals.str.match(rx).mean() >= 0.6

    # Light auto-parse für offensichtliche Datetime-Object-Spalten (nicht-destruktiv)
    if len(dtype_summary['datetime']) == 0:
        for c in df.columns:
            if df[c].dtype == 'object' and _looks_like_datetime_series(df[c]):
                try:
                    # Unterdrücke laute UserWarnings; parse tolerant
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        parsed = pd.to_datetime(df[c], errors='coerce')
                    if parsed.notna().mean() > 0.9:
                        df[c] = parsed
                except Exception:
                    pass
        dtype_summary['datetime'] = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    # Count missing values per column and duplicate rows
    missing_counts = df.isnull().sum()
    duplicate_rows = df.duplicated().sum()

    # Unique counts per column
    unique_counts = df.nunique()
    constant_cols = unique_counts[unique_counts == 1].index.tolist()
    high_cardinality_cols = unique_counts[(unique_counts > 50) | (unique_counts / max(len(df), 1) > 0.30)].index.tolist()

    # If supervised, validate target and check for class imbalance
    imbalance_flag = False
    class_counts = None
    if task_type in ['supervised', 'unsupervised'] and target:
        if target not in df.columns:
            raise ValueError('Target column not found in DataFrame.')
        class_counts = df[target].value_counts()
        if len(class_counts) > 0:
            minority_share = class_counts.min() / class_counts.sum()
            imbalance_flag = minority_share < imbalance_threshold

    # Check for data leakage candidates
    tlow = str(target).lower() if target else None
    leakage_candidates = []
    for col in df.columns:
        clow = col.lower()
        if ('timestamp' in clow) or ('ts_' in clow) or ('_dt' in clow) or (tlow and tlow in clow) or ('target' in clow) or (clow.endswith('_id')):
            leakage_candidates.append(col)

    # Produce cleaning recommendations
    cleaning_recommendations = []
    if missing_counts.any():
        cleaning_recommendations.append('Address missing values.')
    if duplicate_rows > 0:
        cleaning_recommendations.append('Remove duplicate rows.')
    if constant_cols:
        cleaning_recommendations.append('Consider removing constant columns: {}'.format(constant_cols))
    if high_cardinality_cols:
        cleaning_recommendations.append('Review high-cardinality columns: {}'.format(high_cardinality_cols))
    if imbalance_flag:
        cleaning_recommendations.append('Imbalanced classes detected in target. Consider resampling or generating synthetic data.')
    if leakage_candidates:
        cleaning_recommendations.append('Evaluate potential leakage candidates: {}'.format(leakage_candidates))

    # Prepare the output dictionary
    dataset_header = {
        'num_rows': len(df),
        'num_columns': len(df.columns),
        'column_types': {k: str(v) for k, v in dtypes.to_dict().items()}
    }
    data_audit = {
        'missing_counts': missing_counts.to_dict(),
        'duplicate_rows': int(duplicate_rows),
        'unique_counts': unique_counts.to_dict(),
        'constant_cols': constant_cols,
        'high_cardinality_cols': high_cardinality_cols,
        'class_counts': class_counts.to_dict() if class_counts is not None else None,
        'imbalance_flag': bool(imbalance_flag),
        'leakage_candidates': leakage_candidates
    }

    return {
        'dataset_header': dataset_header,
        'data_audit': data_audit,
        'cleaning_recommendations': cleaning_recommendations
    }
