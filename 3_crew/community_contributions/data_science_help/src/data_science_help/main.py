import warnings
from pathlib import Path

from data_science_help.crew import DataScienceTeam

warnings.filterwarnings('ignore', category = SyntaxWarning, module = 'pysbd')


analyze_requirements = [
    
    'Infer dtypes (numeric/categorical/bool/datetime) and list columns per dtype',
    'Report exact counts: missing per column, duplicate rows.',
    'Compute unique_counts per column, flag constant columns (n_unique == 1)',
    'Flag high_cardinality categorical columns (n_unique > 50 or n_unique/n_rows > 0.30).',
    'If supervised: validate target exists, report class counts; set imbalance_flag if minority_share < 0.20.',
    'Check obvious leakage candidates (columns containing target name or post-outcome timestamps); list suspects only (no changes).',
    'Produce cleaning_recommendations as ordered bullets.',
    'Do NOT modify data; return AnalysisKit (DatasetHeader + DataAudit).'
]


research_requirements = [

    'A report that helps understanding the data and know in the cleaning process what is in important considering the specific domain',
    'Give concise domain overview.',
    'List key regulators/standards/frameworks relevant to data use.',
    'Identify sensitive_fields (PII/compliance) commonly present, name typical column labels to watch.',
    'Highlight common_pitfalls for data/label leakage and quality issues in this domain.',
    'List 3-5 typical KPIs used by practioners (context only).',
    'Provide 5-7 citations (title + url) from diverse, authoritative sources; add publication date if available.',
    'Set confidence in [0,1] based on source quality/diversity/agreement.',
    'If company provided: add company_notes (business model, data specifics); else skip company section (do not guess!).',
]



def ensure_dirs():
    for p in [
        Path('outputs'),
        Path('outputs/plots'),
        Path('outputs/step_audits'),
    ]:
        p.mkdir(parents = True, exist_ok = True)

def base_inputs():
    """Static baseline config used by the UI to build full `inputs`."""
    return {
        'analyze_requirements': analyze_requirements,

        'analyze_module': 'analysis.py',
        'cleaning_module': 'cleaning.py',
        'viz_module': 'viz.py',

        'cleaning_class': 'DataCleaner',
        'viz_class': 'VizToolKit',

    }

def run():
    ensure_dirs()

    result = DataScienceTeam().crew().kickoff(inputs = base_inputs())
    return result

if __name__ == '__main__':
    run()