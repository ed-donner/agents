from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal, Any


# --- Design Output ---

class FunctionSpec(BaseModel):
    name: str
    signature: str                       # e.g. "run_analysis(csv_file, task_type, target=None, imbalance_threshold=0.2)"
    inputs: List[str]
    outputs: List[str]
    side_effects: Optional[List[str]]# e.g. ["writes outputs/analysis.json"]

class ClassSpec(BaseModel):
    name: str
    methods: List[FunctionSpec]

class ModuleSpec(BaseModel):
    name: str
    classes: Optional[List[ClassSpec]] 
    functions: Optional[List[FunctionSpec]] 
    notes: Optional[List[str]] 

class SystemDesign(BaseModel):
    modules: List[ModuleSpec]
    assumptions: Optional[List[str]]
    risks: Optional[List[str]] 
    artifacts: Optional[List[str]] 



# -- Analysis Output --- 

class DatasetAudit(BaseModel):
    path: str = Field(description = 'Given csv path as a string')
    csv_name: str = Field(description = 'Basename of the csv data without .csv ending')
    n_rows: int
    n_cols: int
    columns: List[str]
    numeric_cols: List[str]
    categorical_cols: List[str]
    task_type: str = Field(description = 'e.g. unsupervised, supervised, not_sure, semi-supervised')
    target: str = Field(description = 'Just if task_type = supervised')
    domain: str = Field(description = 'Domain is optional given by the user')
    company: str = Field(description = 'Company is optional given by the user')
    missing_counts: Dict[str, int] = Field(..., description = 'Absolute number of missing values per column (key = column name, value = count)')
    duplicate_rows: int = Field(..., description = 'Exact count of fully duplicated rows in the dataset')
    unique_counts: Dict[str, int] = Field(..., description = 'Absolute number of unique values per column (key = column name, value = count)')
    cleaning_recommendations: List[str] = Field(..., description = 'Ordered list of concrete, reversible cleaning suggestions derived from the audit.')
    constant_cols: List[str] = Field(description = 'Columns with zero variance (exactly one unique value across all rows)')
    high_card_col: List[str] = Field(description = 'Categorical columns with unusually many distinct values (e.g., n_unique > 50 or n_unique/n_rows > 0.30).')
    module_path: str = Field(..., description = 'Filesystem path to the gnerated analysis module (e.g., outputs/analysis.py)') 


# --- Report Output & Validator ---

class ReportCitation(BaseModel):
    title: str = Field(..., description = 'Title of cited page/report.')
    url: str = Field(..., description = 'URL of the source')
    source: Optional[str] = Field(description = 'Short source/domain label')
    date: Optional[str] = Field(description = 'Publication date or year if available (e.g., 2023-11-29 or 2023)')

class ReportScope(BaseModel):
    value: Literal['domain_only', 'domain_plus_company'] = Field(..., description = 'Scope the report: domain_only or domain_plus_company')


class DomainReport(BaseModel):
    scope: ReportScope = Field(..., description = 'Indicates if the report covers only the domain or domain plus company')
    key_findings: List[str] = Field(..., description = 'Give 5-10 insights about the domain and if given company')
    pitfalls: List[str] = Field(..., description = 'Typical data pitfalls with one line context')
    sensitive_fields: List[str] = Field(description = 'Fields with PII/compliance relevance.')
    kpis: List[str] = Field(..., description = '3-5 KPIs relevant to the domain')
    citations: List[ReportCitation] = Field(description = 'List of sources used for the report.')
    confidence: float = Field(..., ge = 0.0, le = 1.0,
        description = 'Confidence score in [0, 1] based on source quality, diversity and agreement')

    @validator('citations')
    def min_citations_require(cls, v: List[ReportCitation]) -> List[ReportCitation]:
        if len(v) < 5:
            raise ValueError('At least 5 citations are required')
        return v

    @validator('key_findings')
    def limit_key_findings(cls, v: List[str]) -> List[str]:
        if not (5 <= len(v) <= 10):
            raise ValueError('key_findings should contain between 5 and 10 items')
        return v

    @validator('kpis')
    def limit_kpis(cls, v: List[str]) -> List[str]:
        if not (1 <= len(v) <= 10):
            raise ValueError('kpis should contain between 1-10 items. Aim at least for 5')
        return v 


# --- Cleaning Output & Validator --- 
class CleaningAction(BaseModel):
    type: Literal[
        'impute',
        'drop_cols',
        'drop_rows',
        'dedupe',
        'convert_dtype',
        'fillna',
        'custom'
    ] = Field(..., description = 'Action kind to apply in the cleaning pipeline')

    params: Dict[str, Any] = Field(..., description = 'Action parameters (e.g., {"strategy": "median"})')
    rationale: str = Field(..., description = 'Short justification for why this action is needed')


class CleaningPlan(BaseModel):
    actions: List[CleaningAction] = Field(..., description = 'Ordered list of reversible cleaning actions')
    risk_level: Literal['low', 'medium', 'high'] = Field(..., description = 'Overall risk of information loss due to the plan')
    reversible: bool = Field(True, description = 'Whether the plan keeps originals/logs so changes are reversible')


    @validator('actions')
    def action_require(cls, v: List[CleaningAction]) -> List[CleaningAction]:
        if len(v) == 0:
            raise ValueError('CleaningPlan.actions must contain at least 1 CleaningAction')
        return v


class CleanedDataRef(BaseModel):
    df_alias: str = Field(..., description = 'In-memory alias for the cleaned DataFrame (e.g., cleaned_<csv_name>)')
    rows: int = Field(..., description = 'Row count of the cleaned DataFrame')
    cols: int = Field(..., description = 'Column count of the cleaned DataFrame')
    before_after_stats: Dict[str, int] = Field(..., description = "Key before/after counters to prove effects, e.g.: "
            "{'before_rows':..., 'after_rows':..., 'before_missing':..., 'after_missing':..., "
            "'before_dupes':..., 'after_dupes':...}")
    artifact_path: str = Field(..., description = 'Filesystem path to the persisted cleaned CSV')
    module_path: str = Field(..., description = 'Path to the cleaning module that executed the plan')


    @validator('before_after_stats')
    def check_keys(cls, v: Dict[str, int]) -> Dict[str, int]:
        expected = {'before_rows', 'after_rows'}
        if not expected.issubset(v.keys()):
            raise ValueError('before_after_stats should include at least before_rows and after_rows')
        return v


class CleaningWrapper(BaseModel):
    plan: CleaningPlan
    ref: CleanedDataRef


# --- Visualization Output & Validator--- 

class FigPaths(BaseModel):
    target_distribution: Optional[str] = Field(description = 'PNG path for target distribution (only for supervised tasks).')
    missing_rates: Optional[str] = Field(description="PNG path for per-column missingness visualization.")
    correlation_heatmap: Optional[str] = Field(description="PNG path for numeric correlation heatmap.")
    numeric_hists: Optional[List[str]] = Field(description="List of PNG paths for numeric histograms.")
    boxplots: Optional[List[str]] = Field(description="List of PNG paths for boxplots of numeric features.")
    category_bars: Optional[List[str]] = Field(description="List of PNG paths for categorical bar charts.")

    @validator('numeric_hists', 'boxplots', 'category_bars')
    def empty_lists_to_none(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if isinstance(v, list) and len(v) == 0:
            return None
        return v

class VisualSummary(BaseModel):
    fig_paths: FigPaths = Field(..., description = 'Filesystem paths of all generated figures. PNG only (no inline figures)')
    quick_insights: List[str] = Field(..., description = '2-5 concise bullets summarizing the main patterns seen in the plots')
    imbalance_flag: bool = Field(..., description="True if class imbalance is flagged by policy (e.g., minority share below threshold).")
    module_path: str = Field(..., description = 'Path to visualization module used to generate figures (e.g., <viz_module>.py)')
    
    @validator("fig_paths")
    def ensure_one_figure(cls, v: FigPaths) -> FigPaths:

        has_any = any([
            bool(v.target_distribution),
            bool(v.missing_rates),
            bool(v.correlation_heatmap),
            bool(v.numeric_hists and len(v.numeric_hists) > 0),
            bool(v.boxplots and len(v.boxplots) > 0),
            bool(v.category_bars and len(v.category_bars) > 0),
        ])
        if not has_any:
            raise ValueError("VisualSummary.fig_paths must contain at least one figure path.")
        return v


# --- Controller Output & Validator ---

class StepAudit(BaseModel):
    step_name: str = Field(..., description = 'Name of audited step/task, e.g., analyze_task.')
    status: Literal['passed', 'retry', 'failed'] = Field(..., description = 'Controller decision for this step.')
    issues: List[str] = Field(..., description = 'Up to 3 short, concrete problems cetected during audit.')
    recommendation: str = Field(..., description = 'Single, specific next action to address the issues.')
    evidence: List[str] = Field(..., description = 'Key numbers/field names/paths supporting the decisions.')
    timestamp_utc: Optional[str] = Field(description='ISO-8601 UTC timestamp set by controller.')


    @validator('recommendation')
    def _non_empty_reco(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Recommendation must be a non-empty string.")
        return v